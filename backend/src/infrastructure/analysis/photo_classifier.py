import os
import re
import json
import logging
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import cv2
import numpy as np

from .reference_matcher import extract_features

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

# Categories a photo can plausibly be reassigned within if its detected
# position is already taken by another photo in the same batch. Kept as a
# short allow-list (not the full position space) so a driver photo, say,
# never gets forced onto "kit de carretera" just because that slot is free.
COLLISION_ALLOW_LIST = {
    1: [11], 11: [1],
    2: [3, 6], 3: [2, 6, 7], 4: [5], 5: [4],
    6: [2, 3, 7], 7: [3, 6],
    8: [],
    9: [10], 10: [9],
}

# Feature keys used to compare a contested photo against each position's
# reference profile when resolving collisions (see _find_alternative_position).
SIMILARITY_FEATURE_KEYS = [
    "brightness", "sat_mean", "hue_mean", "blue_ratio",
    "edge_pct", "laplacian_var", "aspect_ratio", "sky_blue_ratio",
]

DEFAULT_PROFILES_PATH = os.path.join(os.path.dirname(__file__), "position_profiles.json")


class PhotoClassifier:
    def __init__(self, reference_dir: str = None):
        self._face_cascade = None
        self._cache: dict[str, dict] = {}
        self._position_profiles = self._load_position_profiles(reference_dir)

    def _get_face_cascade(self):
        if self._face_cascade is None:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self._face_cascade = cv2.CascadeClassifier(cascade_path)
        return self._face_cascade

    # ---- position similarity profiles (used by collision resolution) ----

    def _load_position_profiles(self, reference_dir: Optional[str]) -> dict[int, np.ndarray]:
        if reference_dir and os.path.isdir(reference_dir):
            try:
                built = self._build_profiles_from_dir(reference_dir)
                if built:
                    return built
            except Exception as e:
                logger.warning(f"Could not build position profiles from {reference_dir}: {e}")

        if os.path.exists(DEFAULT_PROFILES_PATH):
            try:
                with open(DEFAULT_PROFILES_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return {int(k): np.array(v, dtype=float) for k, v in data.items()}
            except Exception as e:
                logger.warning(f"Could not load default position profiles: {e}")

        return {}

    def _build_profiles_from_dir(self, directory: str) -> dict[int, np.ndarray]:
        profiles: dict[int, np.ndarray] = {}
        for entry in os.listdir(directory):
            full_path = os.path.join(directory, entry)
            if not os.path.isdir(full_path):
                continue
            match = re.match(r"^\s*(\d{1,2})", entry)
            if not match:
                continue
            pos_num = int(match.group(1))
            if pos_num not in INSPECTION_POSITIONS:
                continue

            vectors = []
            for fname in os.listdir(full_path):
                fpath = os.path.join(full_path, fname)
                feats = extract_features(fpath)
                if feats is None:
                    continue
                vectors.append([feats.get(k, 0.0) for k in SIMILARITY_FEATURE_KEYS])

            if vectors:
                profiles[pos_num] = np.mean(np.array(vectors, dtype=float), axis=0)

        return profiles

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
        cached = self._cache.get(image_path)
        if cached and "features" in cached:
            features = cached["features"]
        else:
            features = extract_features(image_path)
            if features is None:
                return None, {"method": "unreadable", "confidence": "low"}
            self._cache.setdefault(image_path, {})["features"] = features

        result = self._detect_document_group(features, image_path)
        if result:
            return result

        result = self._detect_driver_group(features, image_path)
        if result:
            return result

        result = self._detect_carparts_group(features, image_path)
        if result:
            return result

        result = self._detect_exterior_group(features, image_path)
        if result:
            return result

        return None, {"method": "unclassified", "confidence": "low"}

    def classify_batch(self, image_paths: list[str]) -> dict:
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

        used_positions: set[int] = set()
        assignments: dict[str, dict] = {}

        for idx, pos, info in results:
            path = image_paths[idx]
            if pos is not None and pos not in used_positions:
                assignments[path] = {"position": pos, "info": info}
                used_positions.add(pos)
            elif pos is not None and pos in used_positions:
                features = self._cache.get(path, {}).get("features")
                alt = self._find_alternative_position(pos, used_positions, features)
                if alt:
                    alt_pos, margin_ratio = alt
                    conf, m = self._margin_to_confidence(margin_ratio)
                    assignments[path] = {
                        "position": alt_pos,
                        "info": {"method": "alternative_position", "confidence": conf, "margin": m},
                    }
                    used_positions.add(alt_pos)
                else:
                    assignments[path] = {"position": None, "info": {"method": "position_taken_no_alternative", "confidence": "low"}}
            else:
                assignments[path] = {"position": None, "info": info}

        self._cache.clear()
        return assignments

    def _find_alternative_position(self, original_pos: int, used: set[int], features: Optional[dict]) -> Optional[tuple[int, float]]:
        candidates = [p for p in COLLISION_ALLOW_LIST.get(original_pos, []) if p not in used]
        if not candidates:
            return None

        if not features or not self._position_profiles:
            # No similarity data available: fall back to the first plausible
            # candidate with a conservative (low) confidence margin.
            return candidates[0], 0.0

        vec = np.array([features.get(k, 0.0) for k in SIMILARITY_FEATURE_KEYS], dtype=float)

        best_pos, best_similarity = None, None
        for pos in candidates:
            profile = self._position_profiles.get(pos)
            if profile is None:
                continue
            norm = np.abs(profile) + 1e-6
            dist = float(np.linalg.norm((vec - profile) / norm))
            similarity = 1.0 / (1.0 + dist)
            if best_similarity is None or similarity > best_similarity:
                best_similarity, best_pos = similarity, pos

        if best_pos is None:
            return candidates[0], 0.0

        # similarity is in (0, 1]; treat it directly as a margin ratio for
        # confidence bucketing (closer match to the position's profile ->
        # higher confidence in the reassignment).
        return best_pos, best_similarity

    def _detect_document_group(self, features: dict, image_path: str) -> Optional[tuple]:
        b = features["brightness"]
        bm = features["brightness_median"]
        wr = features["white_ratio"]
        lap = features["laplacian_var"]

        text_regions, text_length = self._detect_text_density(image_path)
        has_meaningful_text = text_regions >= 2 and text_length >= 50

        if not has_meaningful_text:
            return None

        # Absolute brightness floor for "bright scanned document", relaxed for
        # photos whose overall exposure is objectively low (so a dim-lit
        # document photo isn't rejected just for being underexposed).
        bright_floor = min(160.0, max(120.0, bm * 1.4))
        if wr > 0.15 and b > bright_floor:
            margin = min(
                self._margin_ratio(wr, 0.15, 0.15),
                self._margin_ratio(b, bright_floor, 60),
            )
            conf, m = self._margin_to_confidence(margin)
            if text_regions >= 4 and text_length >= 200:
                return 1, {"method": "structured_form", "confidence": conf, "margin": m, "text_regions": text_regions, "text_length": text_length}
            return 11, {"method": "document_text", "confidence": conf, "margin": m, "text_regions": text_regions, "text_length": text_length}

        dim_floor = max(100.0, bm * 1.1)
        if b > dim_floor and lap < 700:
            margin = min(
                self._margin_ratio(b, dim_floor, 60),
                self._margin_ratio(lap, 700, 400, greater=False),
            )
            conf, m = self._margin_to_confidence(margin)
            if text_regions >= 3:
                return 1, {"method": "form_medium_text", "confidence": conf, "margin": m, "text_regions": text_regions}
            return 11, {"method": "document_medium_text", "confidence": conf, "margin": m, "text_regions": text_regions}

        return None

    def _detect_driver_group(self, features: dict, image_path: str) -> Optional[tuple]:
        if self._detect_face(image_path):
            return 8, {"method": "face_detected", "confidence": "high", "margin": 1.0}

        b = features["brightness"]
        bl = features["blue_ratio"]
        cb = features["center_brightness"]
        cst = features["center_std"]
        bm = features["brightness_median"]
        mad = features["brightness_mad"]

        # Center-of-frame darker than the photo's own typical brightness by a
        # robust margin, rather than a fixed absolute constant.
        dark_center_floor = bm - max(1.2 * mad, 15.0)
        if bl < 0.30 and b < 130 and cb < dark_center_floor and cst < 85:
            if self._detect_face(image_path, min_size=(60, 60)):
                return 8, {"method": "face_indoor_dark", "confidence": "high", "margin": 1.0}

        return None

    def _detect_exterior_group(self, features: dict, image_path: str) -> Optional[tuple]:
        b = features["brightness"]
        sky = features["sky_blue_ratio"]
        orient = features["orientation"]
        sat = features["sat_mean"]
        bl = features["blue_ratio"]
        tb_ratio = features["top_bottom_brightness_ratio"]

        gate_margin = None

        if sky > 0.05 and (b > 110 or tb_ratio > 1.05):
            gate_margin = min(
                self._margin_ratio(sky, 0.05, 0.05),
                max(self._margin_ratio(b, 110, 60), self._margin_ratio(tb_ratio, 1.05, 0.3)),
            )
        elif b > 130 and sat > 30 and bl > 0.18:
            gate_margin = min(
                self._margin_ratio(b, 130, 60),
                self._margin_ratio(sat, 30, 30),
                self._margin_ratio(bl, 0.18, 0.15),
            )
        elif b > 100 and sat > 35 and orient == "landscape":
            gate_margin = min(
                self._margin_ratio(b, 100, 60),
                self._margin_ratio(sat, 35, 30),
            )
        elif b > 140 and bl > 0.20:
            gate_margin = min(
                self._margin_ratio(b, 140, 60),
                self._margin_ratio(bl, 0.20, 0.15),
            )

        if gate_margin is None:
            return None

        return self._classify_exterior_subtype(features, image_path, gate_margin)

    def _classify_exterior_subtype(self, features: dict, image_path: str, gate_margin: float = 0.0) -> Optional[tuple]:
        img = cv2.imread(image_path)
        if img is None:
            return None
        h, w, _ = img.shape
        if max(h, w) > 800:
            scale = 800 / max(h, w)
            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
            h, w, _ = img.shape

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        symmetry = self._compute_horizontal_symmetry(gray)
        headlights = self._detect_headlights(gray, img)
        taillights = self._detect_taillights(img)
        left_side = self._detect_side_view(gray, side="left")
        right_side = self._detect_side_view(gray, side="right")

        orient = features["orientation"]
        ar = features["aspect_ratio"]

        if headlights and symmetry > 0.8 and orient == "landscape":
            conf, m = self._margin_to_confidence(min(gate_margin, self._margin_ratio(symmetry, 0.8, 0.2)))
            return 2, {"method": "frontal_symmetry_headlights", "confidence": conf, "margin": m, "symmetry": round(symmetry, 3)}
        if taillights and symmetry > 0.8 and orient == "landscape":
            conf, m = self._margin_to_confidence(min(gate_margin, self._margin_ratio(symmetry, 0.8, 0.2)))
            return 6, {"method": "rear_symmetry_taillights", "confidence": conf, "margin": m, "symmetry": round(symmetry, 3)}
        if symmetry > 0.85 and ar < 1.4:
            conf, m = self._margin_to_confidence(min(gate_margin, self._margin_ratio(symmetry, 0.85, 0.15)))
            return 2, {"method": "high_symmetry_frontal", "confidence": conf, "margin": m, "symmetry": round(symmetry, 3)}
        if symmetry > 0.8 and ar < 1.4:
            conf, m = self._margin_to_confidence(min(gate_margin, self._margin_ratio(symmetry, 0.8, 0.2)))
            return 6, {"method": "high_symmetry_rear", "confidence": conf, "margin": m, "symmetry": round(symmetry, 3)}

        if left_side and ar > 1.6:
            conf, m = self._margin_to_confidence(min(gate_margin, self._margin_ratio(ar, 1.6, 0.6)))
            return 4, {"method": "left_side_profile", "confidence": conf, "margin": m}
        if right_side and ar > 1.6:
            conf, m = self._margin_to_confidence(min(gate_margin, self._margin_ratio(ar, 1.6, 0.6)))
            return 5, {"method": "right_side_profile", "confidence": conf, "margin": m}

        # Intermediate 3/4-angle band between pure frontal/rear symmetry and a
        # pure side profile — covers positions 3 ("Frontal lateral") and 7
        # ("Lateral trasera"), which no prior detector ever produced.
        if 0.5 < symmetry <= 0.8 and 1.2 < ar <= 1.6:
            band_margin = min(
                gate_margin,
                self._margin_ratio(symmetry, 0.5, 0.3),
                self._margin_ratio(ar, 1.6, 0.4, greater=False),
            )
            conf, m = self._margin_to_confidence(band_margin)
            if headlights:
                return 3, {"method": "three_quarter_front", "confidence": conf, "margin": m, "symmetry": round(symmetry, 3), "aspect_ratio": ar}
            if taillights:
                return 7, {"method": "three_quarter_rear", "confidence": conf, "margin": m, "symmetry": round(symmetry, 3), "aspect_ratio": ar}

        if ar > 1.6:
            conf, m = self._margin_to_confidence(min(gate_margin, self._margin_ratio(ar, 1.6, 0.6)))
            return 4, {"method": "side_aspect_ratio", "confidence": conf, "margin": m, "aspect_ratio": ar}

        if symmetry > 0.7:
            conf, m = self._margin_to_confidence(min(gate_margin, self._margin_ratio(symmetry, 0.7, 0.3)))
            return 2, {"method": "moderate_symmetry_frontal", "confidence": conf, "margin": m, "symmetry": round(symmetry, 3)}

        return None

    def _compute_horizontal_symmetry(self, gray: np.ndarray) -> float:
        h, w = gray.shape
        mid = w // 2
        left = gray[:, :mid]
        right = cv2.flip(gray[:, mid + (w % 2):], 1)
        if left.shape != right.shape:
            min_w = min(left.shape[1], right.shape[1])
            left = left[:, :min_w]
            right = right[:, :min_w]
        diff = cv2.absdiff(left, right)
        return float(1.0 - np.mean(diff) / 255.0)

    def _detect_headlights(self, gray: np.ndarray, color: np.ndarray) -> bool:
        h, w = gray.shape
        bottom = gray[3 * h // 4:, :]
        blurred = cv2.GaussianBlur(bottom, (15, 15), 0)
        # Bright-spot threshold relative to this photo's own top-percentile
        # brightness instead of a fixed absolute 230, so underexposed
        # headlight shots aren't silently missed.
        thresh_val = max(150.0, float(np.percentile(blurred, 99)) - 5)
        _, bright_spots = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY)
        spot_pct = float(np.mean(bright_spots > 0))
        if 0.01 < spot_pct < 0.15:
            bottom_color = color[3 * h // 4:, :, :]
            white_pct = float(np.mean(np.all(bottom_color > 200, axis=2)))
            if white_pct > 0.02:
                return True
        return False

    def _detect_taillights(self, color: np.ndarray) -> bool:
        h, w, _ = color.shape
        bottom = color[3 * h // 4:, :, :]
        hsv = cv2.cvtColor(bottom, cv2.COLOR_BGR2HSV)
        lower_red = np.array([0, 50, 50])
        upper_red = np.array([10, 255, 255])
        mask1 = cv2.inRange(hsv, lower_red, upper_red)
        lower_red2 = np.array([160, 50, 50])
        upper_red2 = np.array([180, 255, 255])
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        red_mask = mask1 | mask2
        red_pct = float(np.mean(red_mask > 0))
        return red_pct > 0.01 and red_pct < 0.20

    def _detect_side_view(self, gray: np.ndarray, side: str = "left") -> bool:
        h, w = gray.shape
        third = w // 3
        if side == "left":
            region = gray[:, :third]
        else:
            region = gray[:, -third:]
        blurred = cv2.medianBlur(region, 15)
        circles = cv2.HoughCircles(
            blurred, cv2.HOUGH_GRADIENT, dp=1.2, minDist=30,
            param1=50, param2=25, minRadius=int(h * 0.05), maxRadius=int(h * 0.35)
        )
        if circles is not None:
            return True

        edges = cv2.Canny(region, 30, 100)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=80, minLineLength=40, maxLineGap=20)
        if lines is not None and len(lines) > 5:
            return True

        return False

    def _detect_carparts_group(self, features: dict, image_path: str) -> Optional[tuple]:
        b = features["brightness"]
        ep = features["edge_pct"]
        lap = features["laplacian_var"]
        sat = features["sat_mean"]
        orient = features["orientation"]

        if b > 130:
            return None

        img = cv2.imread(image_path)
        if img is None:
            return None
        h, w, _ = img.shape
        if max(h, w) > 800:
            scale = 800 / max(h, w)
            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
            h, w, _ = img.shape

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        blurred = cv2.medianBlur(gray, 15)
        circles = cv2.HoughCircles(
            blurred, cv2.HOUGH_GRADIENT, dp=1.3, minDist=50,
            param1=50, param2=30, minRadius=int(min(h, w) * 0.05), maxRadius=int(min(h, w) * 0.4)
        )
        has_wheel = circles is not None

        red_mask = cv2.inRange(hsv, np.array([0, 30, 30]), np.array([10, 255, 255]))
        red_mask |= cv2.inRange(hsv, np.array([160, 30, 30]), np.array([180, 255, 255]))
        red_pct = float(np.mean(red_mask > 0))

        white_mask = cv2.inRange(gray, 200, 255)
        white_pct = float(np.mean(white_mask > 0))

        is_close_up = has_wheel and b < 100 and orient == "landscape"
        if is_close_up:
            m = min(self._margin_ratio(b, 100, 40, greater=False), 1.0)
            conf, mr = self._margin_to_confidence(m)
            return 10, {"method": "wheel_closeup", "confidence": conf, "margin": mr}

        if b < 100 and ep < 14 and lap < 600:
            base_margin = min(
                self._margin_ratio(b, 100, 40, greater=False),
                self._margin_ratio(ep, 14, 10, greater=False),
                self._margin_ratio(lap, 600, 300, greater=False),
            )
            conf, mr = self._margin_to_confidence(base_margin)
            if ep < 10 and b < 85:
                return 10, {"method": "dark_very_smooth", "confidence": conf, "margin": mr}
            if sat < 55 and red_pct > 0.02:
                return 9, {"method": "dark_red_objects", "confidence": conf, "margin": mr}
            if white_pct > 0.15 and has_wheel:
                return 10, {"method": "dark_white_objects_wheel", "confidence": conf, "margin": mr}
            if has_wheel:
                return 10, {"method": "dark_wheel_detected", "confidence": conf, "margin": mr}
            return 9, {"method": "dark_smooth_indoor", "confidence": conf, "margin": mr}
        if b < 115 and ep < 15 and lap < 700:
            base_margin = min(
                self._margin_ratio(b, 115, 40, greater=False),
                self._margin_ratio(ep, 15, 10, greater=False),
                self._margin_ratio(lap, 700, 300, greater=False),
            )
            conf, mr = self._margin_to_confidence(base_margin)
            if sat < 50:
                return 9, {"method": "carparts_default", "confidence": conf, "margin": mr}
            return 10, {"method": "carparts_saturated", "confidence": conf, "margin": mr}

        return None

    def _detect_face(self, image_path: str, min_size: tuple = (80, 80)) -> bool:
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

        if h < min_size[0] or w < min_size[1]:
            return False

        try:
            cascade = self._get_face_cascade()
            faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=min_size)
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
