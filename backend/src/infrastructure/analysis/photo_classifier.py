import os
import logging
import threading
from collections import defaultdict
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import cv2

from .reference_matcher import extract_features
from .embedding_classifier import confidence_from_prob

# classify_batch runs classify() for up to 8 photos concurrently
# (ThreadPoolExecutor below), but Tesseract is CPU-heavy enough that 8
# concurrent subprocesses starve each other: measured 81/81 OCR timeouts
# under full concurrency vs. 1/81 sequentially (see backend/eval/results/).
# Capping concurrent Tesseract subprocesses independently of the classify
# thread pool keeps CLIP embedding inference (cheap, doesn't need this) at
# full parallelism while OCR gets enough CPU per process to finish.
_OCR_CONCURRENCY = threading.Semaphore(2)

logger = logging.getLogger(__name__)

INSPECTION_POSITIONS = {
    1: "Formato de inspección",
    2: "Frontal",
    3: "Frontal lateral",
    4: "Lado izquierdo",
    5: "Lado derecho",
    6: "Trasera",
    7: "Lateral trasera",
    8: "Conductor",
    9: "Kit de carretera",
    10: "Gato y llanta de repuesto",
    11: "SOAT y documentos",
}

# Max photos classify_batch will assign to a given position before treating
# further matches as collisions. Every position defaults to 1; position 10
# ("Gato y llanta de repuesto") is the one exception, matching the same cap
# enforced on manual assignment in generate.py's MAX_PER_POSITION.
MAX_PER_POSITION = {10: 2}

# _detect_document_override's evidence floor -- also used upfront to decide
# whether extract_features()'s white-balance/CLAHE pass is worth running at
# all (see classify()).
_DOC_TEXT_REGIONS_MIN = 4
_DOC_TEXT_LENGTH_MIN = 200


class PhotoClassifier:
    def __init__(self):
        self._cache: dict[str, dict] = {}
        self._embedding_classifier = None

    # ---- confidence helpers ----

    def _margin_ratio(self, value: float, threshold: float, scale: float, greater: bool = True) -> float:
        scale = scale if abs(scale) > 1e-6 else 1e-6
        if greater:
            return (value - threshold) / scale
        return (threshold - value) / scale

    def _margin_to_confidence(self, margin_ratio: float) -> tuple[str, float]:
        margin_ratio = round(max(margin_ratio, 0.0), 3)
        if margin_ratio >= 0.25:
            return "high", margin_ratio
        if margin_ratio >= 0.08:
            return "medium", margin_ratio
        return "low", margin_ratio

    # ---- classification ----

    def classify(self, image_path: str) -> tuple[Optional[int], dict]:
        """CLIP-embedding classifier (see embedding_classifier.py) is the
        primary decision maker -- measured at 75% cross-validated accuracy
        on session-held-out data, vs. 4.94% for the hand-tuned absolute
        thresholds this replaced (backend/eval/results/). Strong OCR text
        density remains as an override for position 1 (structured forms):
        it's an independent, stronger signal than anything a generic image
        embedding can infer, so a confident hit there should win even when
        it disagrees with the embedding head.

        A Haar cascade face-detection override for position 8 (Conductor)
        was tried and removed: measured after fixing a caching bug that had
        kept it from ever firing in production, it was net-negative --
        position 8 was already 100% accurate from the embedding alone, and
        the cascade's false positives on non-driver photos (wheels, kit
        items) cost 2 correct classifications elsewhere for zero gain (see
        backend/eval/results/).
        """
        if self._load_gray(image_path) is None:
            return None, {"method": "unreadable", "confidence": "low"}

        text_regions, text_length = self._detect_text_density(image_path)
        doc_override = None
        if text_regions >= _DOC_TEXT_REGIONS_MIN and text_length >= _DOC_TEXT_LENGTH_MIN:
            # extract_features() does its own white-balance + CLAHE pass --
            # only worth paying for once the OCR gate already indicates a
            # document-shaped photo, since _detect_document_override always
            # rejects anything below this same threshold anyway.
            features = extract_features(image_path)
            if features is not None:
                doc_override = self._detect_document_override(features, text_regions, text_length)
        if doc_override:
            return doc_override

        return self._get_embedding_classifier().classify(image_path)

    def classify_batch(self, image_paths: list[str]) -> dict:
        """Runs classify() per photo, then resolves position collisions with
        a deterministic global assignment instead of a hand-written adjacency
        map. Every (photo, position) pair the embedding classifier scored is
        a candidate; the OCR document override contributes its single
        winning position at probability 1.0, since it's independent,
        stronger evidence than the embedding for the position it fires on.
        All
        candidates are sorted by probability, then assigned greedily -- the
        photo most confident about a slot claims it first. This replaced a
        hardcoded COLLISION_ALLOW_LIST (e.g. "if position 8 is taken, there
        is no fallback") plus a same-batch reassignment scored against
        reference_matcher features, which measured 66.67% with 16% of
        photos left unassigned on the 81-photo eval set -- almost entirely
        from collisions the allow-list had no answer for (see
        backend/eval/results/). This scores 88.89% at the per-photo level;
        the ~10-point gap that remains here is inherent to batch collisions,
        not an artifact of the old adjacency map.
        """
        n = len(image_paths)
        results: list[tuple[int, Optional[int], dict]] = [None] * n

        with ThreadPoolExecutor(max_workers=min(8, n)) as executor:
            fut_map = {executor.submit(self.classify, image_paths[i]): i for i in range(n)}
            for fut in as_completed(fut_map):
                idx = fut_map[fut]
                try:
                    pos, info = fut.result()
                    results[idx] = (idx, pos, info)
                except Exception as e:
                    logger.warning(f"Classify failed for {image_paths[idx]}: {e}")
                    results[idx] = (idx, None, {"method": "error", "confidence": "low"})

        # Build every (photo_idx, position, probability, info) candidate.
        candidates: list[tuple[int, int, float, dict]] = []
        for idx, pos, info in results:
            if pos is None:
                continue
            probs = info.get("probs")
            if probs:
                for pos_str, p in probs.items():
                    candidates.append((idx, int(pos_str), float(p), info))
            else:
                # The OCR override (and any method without a full
                # distribution) only offers its single winning position,
                # treated as maximally confident.
                candidates.append((idx, pos, 1.0, info))

        candidates.sort(key=lambda c: c[2], reverse=True)

        position_counts: dict[int, int] = defaultdict(int)
        assigned_idx: set[int] = set()
        assignments: dict[str, dict] = {}

        for idx, pos, prob, info in candidates:
            if idx in assigned_idx:
                continue
            if position_counts[pos] >= MAX_PER_POSITION.get(pos, 1):
                continue
            path = image_paths[idx]
            if pos == results[idx][1]:
                # This candidate is the photo's own top prediction -- keep
                # its original info (method/confidence) as reported by classify().
                assignments[path] = {"position": pos, "info": info}
            else:
                assignments[path] = {
                    "position": pos,
                    "info": {"method": "global_assignment", "confidence": confidence_from_prob(prob), "margin": round(prob, 4)},
                }
            position_counts[pos] += 1
            assigned_idx.add(idx)

        for idx, pos, info in results:
            if idx not in assigned_idx:
                path = image_paths[idx]
                assignments[path] = {"position": None, "info": {"method": "no_slot_available", "confidence": "low"}}

        self._cache.clear()
        return assignments

    def _detect_document_override(self, features: dict, text_regions: int, text_length: int) -> Optional[tuple]:
        """Only the strongest OCR evidence tier overrides the embedding
        classifier -- weaker text signals (a stray label, a sticker) are
        left to the embedding, which already classifies documents (pos 1
        and 11) at 100% on held-out data without needing OCR at all."""
        if text_regions < _DOC_TEXT_REGIONS_MIN or text_length < _DOC_TEXT_LENGTH_MIN:
            return None

        b = features["brightness"]
        bm = features["brightness_median"]
        wr = features["white_ratio"]
        bright_floor = min(160.0, max(120.0, bm * 1.4))
        if not (wr > 0.15 and b > bright_floor):
            return None

        margin = min(
            self._margin_ratio(wr, 0.15, 0.15),
            self._margin_ratio(b, bright_floor, 60),
        )
        conf, m = self._margin_to_confidence(margin)
        return 1, {"method": "structured_form_override", "confidence": conf, "margin": m,
                   "text_regions": text_regions, "text_length": text_length}

    def _get_embedding_classifier(self):
        if self._embedding_classifier is None:
            from .embedding_classifier import EmbeddingPositionClassifier
            self._embedding_classifier = EmbeddingPositionClassifier()
        return self._embedding_classifier

    def _load_gray(self, image_path: str):
        """Loads and grayscales an image once per instance, caching it so a
        batch of overrides on the same photo doesn't re-decode the file.
        Returns None if the file can't be read."""
        cached = self._cache.get(image_path)
        if cached and "gray" in cached:
            return cached["gray"]

        img = cv2.imread(image_path)
        if img is None:
            return None
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        self._cache.setdefault(image_path, {})["gray"] = gray
        return gray

    def _detect_text_density(self, image_path: str) -> tuple[int, int]:
        if os.environ.get("SKIP_OCR_DETECTION"):
            return 0, 0

        gray = self._load_gray(image_path)
        if gray is None:
            return 0, 0

        try:
            import pytesseract
            with _OCR_CONCURRENCY:
                data = pytesseract.image_to_data(gray, lang="spa", config="--psm 6", output_type=pytesseract.Output.DICT, timeout=10)
            text_regions = sum(1 for t in data["text"] if t.strip())
            total_text_length = sum(len(t) for t in data["text"] if t.strip())
            return text_regions, total_text_length
        except RuntimeError as e:
            logger.warning(f"Tesseract timed out for {image_path}: {e}")
            return 0, 0
        except Exception as e:
            logger.debug(f"Text detection failed for {image_path}: {e}")
            return 0, 0
