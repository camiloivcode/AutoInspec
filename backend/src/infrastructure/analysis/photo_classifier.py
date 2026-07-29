import os
import re
import logging
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import cv2

from .reference_matcher import ReferenceMatcher, extract_features

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


class PhotoClassifier:
    def __init__(self, reference_dir: str = "/app/fotos_prueba"):
        self._face_cascade = None
        self.matcher = ReferenceMatcher(reference_dir)
        self._cache: dict[str, dict] = {}

    def _get_face_cascade(self):
        if self._face_cascade is None:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self._face_cascade = cv2.CascadeClassifier(cascade_path)
        return self._face_cascade

    def classify(self, image_path: str) -> tuple[Optional[int], dict]:
        cached = self._cache.get(image_path)
        if cached and "features" in cached:
            features = cached["features"]
        else:
            features = extract_features(image_path)
            if features is None:
                return None, {"method": "unreadable", "confidence": "low"}
            self._cache.setdefault(image_path, {})["features"] = features

        b = features["brightness"]
        ep = features["edge_pct"]
        lap = features["laplacian_var"]
        sat = features["sat_mean"]
        hue = features["hue_mean"]
        bl = features["blue_ratio"]
        cs = features["color_std"]
        cb = features.get("center_brightness", b)

        if lap < 500 and ep < 9:
            if bl > 0.4 and b > 130:
                return 11, {"method": "smooth_bright_paper", "confidence": "high"}
            if b < 125:
                return 10, {"method": "smooth_low_brightness", "confidence": "high"}
            return 10, {"method": "very_smooth", "confidence": "high"}

        if bl > 0.5 and b > 145 and lap > 700:
            return 1, {"method": "bright_blue_paper", "confidence": "high"}

        if bl > 0.4 and b > 130 and lap < 700 and ep < 11:
            return 11, {"method": "bright_blue_paper_low_detail", "confidence": "medium"}

        cst = features.get("center_std", 0)
        if bl < 0.30 and b < 120 and cb < 105 and cst < 80:
            if self._detect_face(image_path):
                return 8, {"method": "face_indoor", "confidence": "high"}

        if ep < 11 and lap < 650 and cs > 70:
            return 9, {"method": "smooth_kit_objects", "confidence": "medium"}

        result = self._match_centroid(features)
        if result is not None:
            return result

        result = self._heuristic(features)
        if result is not None:
            return result

        result = self._ocr_check(image_path, features)
        if result is not None:
            return result

        return None, {"method": "unclassified", "confidence": "low"}

    def _match_centroid(self, features: dict) -> Optional[tuple]:
        if not self.matcher.centroids:
            return None

        knn_result = self.matcher.knn_match(features, k=3)
        if knn_result is not None:
            pos, avg_dist = knn_result
            if avg_dist < 0.20:
                return pos, {"method": "knn_match", "confidence": "high", "distance": round(avg_dist, 3)}
            return pos, {"method": "knn_match", "confidence": "medium", "distance": round(avg_dist, 3)}

        best_pos = None
        best_dist = float("inf")
        for pos, centroid in self.matcher.centroids.items():
            dist = self.matcher._distance_to_centroid(features, centroid)
            if dist < best_dist:
                best_dist = dist
                best_pos = pos

        if best_pos is not None and best_dist <= 0.55:
            return best_pos, {"method": "centroid_fallback", "confidence": "low", "distance": round(best_dist, 3)}
        return None

    def _heuristic(self, features: dict) -> Optional[tuple]:
        b = features["brightness"]
        ep = features["edge_pct"]
        lap = features["laplacian_var"]
        sat = features["sat_mean"]
        hue = features["hue_mean"]
        bl = features["blue_ratio"]
        cs = features["color_std"]
        cb = features.get("center_brightness", b)

        if b < 105:
            if sat > 47:
                return 2, {"method": "dark_high_sat", "confidence": "medium"}
            if cs > 78:
                return 3, {"method": "dark_high_color", "confidence": "medium"}
            return 2, {"method": "dark_default", "confidence": "medium"}

        if ep > 16 and lap > 950:
            if sat > 48:
                return 4, {"method": "high_detail_high_sat", "confidence": "medium"}
            return 5, {"method": "high_detail_low_sat", "confidence": "medium"}

        if ep > 15 and lap > 900 and sat < 45:
            if cs > 75:
                return 5, {"method": "high_detail_low_sat_v2", "confidence": "low"}
            return 4, {"method": "high_detail_low_sat_v2_alt", "confidence": "low"}

        if bl > 0.33:
            if cb < 100:
                return 6, {"method": "blue_sky_dark_center", "confidence": "medium"}
            if ep < 15:
                return 7, {"method": "blue_sky_low_edge", "confidence": "low"}
            return 6, {"method": "blue_sky_medium_edge", "confidence": "low"}

        if cs > 78 and ep > 15:
            if sat > 48:
                return 4, {"method": "high_color_high_edge", "confidence": "low"}
            return 5, {"method": "high_color_high_edge_low_sat", "confidence": "low"}

        if ep < 14:
            if bl > 0.30:
                return 6, {"method": "low_edge_some_blue", "confidence": "low"}
            if sat < 43:
                return 3, {"method": "low_edge_low_sat", "confidence": "low"}
            return 2, {"method": "low_edge_frontal", "confidence": "low"}

        if sat > 45 and hue < 75:
            if lap > 850:
                return 2, {"method": "high_lap_frontal", "confidence": "low"}
            return 3, {"method": "medium_sat_frontal_lateral", "confidence": "low"}

        return None

    def _ocr_check(self, image_path: str, features: dict) -> Optional[tuple]:
        text_regions, text_length = self._detect_text_density(image_path)
        if text_regions == 0 and text_length == 0:
            return None

        lap = features["laplacian_var"]
        b = features["brightness"]
        bl = features["blue_ratio"]

        if text_regions >= 5 and text_length >= 300 and lap > 700:
            return 1, {"method": "dense_form_text", "confidence": "medium"}

        if text_regions >= 3 and text_length < 300 and lap < 650 and b > 130:
            return 11, {"method": "document_text", "confidence": "medium"}

        return None

    def classify_batch(self, image_paths: list[str]) -> dict:
        return self._assign_with_dedup(image_paths)

    def _assign_with_dedup(self, image_paths: list[str]) -> dict:
        n = len(image_paths)
        unassigned = set(range(n))
        assignments: dict[str, dict] = {}
        used_positions: set[int] = set()

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

        for idx, pos, info in results:
            path = image_paths[idx]
            if pos is not None and pos not in used_positions:
                assignments[path] = {"position": pos, "info": info}
                used_positions.add(pos)
                unassigned.discard(idx)

        remaining_positions = [p for p in range(1, 12) if p not in used_positions]

        if unassigned and remaining_positions:
            sorted_unassigned = sorted(unassigned)
            for i, idx in enumerate(sorted_unassigned):
                if i < len(remaining_positions):
                    pos = remaining_positions[i]
                    path = image_paths[idx]
                    assignments[path] = {"position": pos, "info": {"method": "sequential_fallback", "confidence": "low"}}
                    used_positions.add(pos)
                else:
                    path = image_paths[idx]
                    assignments[path] = {"position": None, "info": {"method": "no_position_available", "confidence": "low"}}
        else:
            for idx in unassigned:
                path = image_paths[idx]
                assignments[path] = {"position": None, "info": {"method": "no_position_available", "confidence": "low"}}

        self._cache.clear()
        return assignments

    def _detect_face(self, image_path: str) -> bool:
        cached = self._cache.get(image_path)
        if cached and "gray" in cached:
            gray = cached["gray"]
            h, w = cached.get("shape", (0, 0))
        else:
            img = cv2.imread(image_path)
            if img is None:
                return False
            h, w = img.shape[:2]
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            self._cache.setdefault(image_path, {})["gray"] = gray
            self._cache.setdefault(image_path, {})["shape"] = (h, w)

        if h < 80 or w < 80:
            return False

        try:
            cascade = self._get_face_cascade()
            faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6, minSize=(80, 80))
            return len(faces) > 0
        except Exception as e:
            logger.debug(f"Face detection failed: {e}")
            return False

    def _detect_text_density(self, image_path: str) -> tuple[int, int]:
        cached = self._cache.get(image_path)
        if cached and "gray" in cached:
            gray = cached["gray"]
        else:
            img = cv2.imread(image_path)
            if img is None:
                return 0, 0
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            self._cache.setdefault(image_path, {})["gray"] = gray

        try:
            import pytesseract
            data = pytesseract.image_to_data(gray, lang="spa", config="--psm 6", output_type=pytesseract.Output.DICT)
            text_regions = sum(1 for t in data["text"] if t.strip())
            total_text_length = sum(len(t) for t in data["text"] if t.strip())
            return text_regions, total_text_length
        except Exception as e:
            logger.debug(f"Text detection failed for {image_path}: {e}")
            return 0, 0
