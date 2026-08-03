import os
import re
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

EXTERIOR_POSITIONS = [2, 3, 4, 5, 6, 7]


class PhotoClassifier:
    def __init__(self, reference_dir: str = "/app/fotos_prueba"):
        self._face_cascade = None
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
                alt_pos = self._find_alternative_position(pos, used_positions, features=None)
                if alt_pos:
                    assignments[path] = {"position": alt_pos, "info": {"method": "alternative_position", "confidence": "medium"}}
                    used_positions.add(alt_pos)
                else:
                    assignments[path] = {"position": None, "info": {"method": "position_taken_no_alternative", "confidence": "low"}}
            else:
                assignments[path] = {"position": None, "info": info}

        self._cache.clear()
        return assignments

    def _find_alternative_position(self, original_pos: int, used: set[int], features: dict = None) -> Optional[int]:
        group_map = {
            1: [11], 11: [1],
            2: [3, 6], 3: [2, 7], 4: [5], 5: [4],
            6: [2, 7], 7: [3, 6],
            8: [],
            9: [10], 10: [9],
        }
        alternatives = group_map.get(original_pos, [])
        for alt in alternatives:
            if alt not in used:
                return alt
        return None

    def _detect_document_group(self, features: dict, image_path: str) -> Optional[tuple]:
        b = features["brightness"]
        wr = features["white_ratio"]
        ep = features["edge_pct"]
        lap = features["laplacian_var"]
        bl = features["blue_ratio"]

        text_regions, text_length = self._detect_text_density(image_path)
        has_meaningful_text = text_regions >= 2 and text_length >= 50

        if not has_meaningful_text:
            return None

        if has_meaningful_text and wr > 0.15 and b > 160:
            if text_regions >= 4 and text_length >= 200:
                return 1, {"method": "structured_form", "confidence": "high", "text_regions": text_regions, "text_length": text_length}
            return 11, {"method": "document_text", "confidence": "high", "text_regions": text_regions, "text_length": text_length}

        if has_meaningful_text and b > 130 and lap < 700:
            if text_regions >= 3:
                return 1, {"method": "form_medium_text", "confidence": "medium", "text_regions": text_regions}
            return 11, {"method": "document_medium_text", "confidence": "medium", "text_regions": text_regions}

        return None

    def _detect_driver_group(self, features: dict, image_path: str) -> Optional[tuple]:
        if self._detect_face(image_path):
            return 8, {"method": "face_detected", "confidence": "high"}

        b = features["brightness"]
        bl = features["blue_ratio"]
        cb = features["center_brightness"]
        cst = features["center_std"]

        if bl < 0.30 and b < 130 and cb < 110 and cst < 85:
            if self._detect_face(image_path, min_size=(60, 60)):
                return 8, {"method": "face_indoor_dark", "confidence": "high"}

        return None

    def _detect_exterior_group(self, features: dict, image_path: str) -> Optional[tuple]:
        b = features["brightness"]
        sky = features["sky_blue_ratio"]
        orient = features["orientation"]
        ar = features["aspect_ratio"]
        sat = features["sat_mean"]
        bl = features["blue_ratio"]

        is_exterior = False

        if sky > 0.05 and b > 110:
            is_exterior = True
            confidence = "high"
        elif b > 130 and sat > 30 and bl > 0.18:
            is_exterior = True
            confidence = "medium"
        elif b > 100 and sat > 35 and orient == "landscape":
            is_exterior = True
            confidence = "medium"
        elif b > 140 and bl > 0.20:
            is_exterior = True
            confidence = "medium"

        if not is_exterior:
            return None

        specific_pos = self._classify_exterior_subtype(features, image_path)
        if specific_pos:
            return specific_pos

        return None

    def _classify_exterior_subtype(self, features: dict, image_path: str) -> Optional[tuple]:
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
            return 2, {"method": "frontal_symmetry_headlights", "confidence": "high", "symmetry": round(symmetry, 3)}
        if taillights and symmetry > 0.8 and orient == "landscape":
            return 6, {"method": "rear_symmetry_taillights", "confidence": "high", "symmetry": round(symmetry, 3)}
        if symmetry > 0.85 and ar < 1.4:
            return 2, {"method": "high_symmetry_frontal", "confidence": "medium", "symmetry": round(symmetry, 3)}
        if symmetry > 0.8 and ar < 1.4:
            return 6, {"method": "high_symmetry_rear", "confidence": "medium", "symmetry": round(symmetry, 3)}

        if left_side and ar > 1.6:
            return 4, {"method": "left_side_profile", "confidence": "high"}
        if right_side and ar > 1.6:
            return 5, {"method": "right_side_profile", "confidence": "high"}

        if ar > 1.6:
            return 4, {"method": "side_aspect_ratio", "confidence": "medium", "aspect_ratio": ar}

        if symmetry > 0.7:
            return 2, {"method": "moderate_symmetry_frontal", "confidence": "low", "symmetry": round(symmetry, 3)}

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
        _, bright_spots = cv2.threshold(blurred, 230, 255, cv2.THRESH_BINARY)
        spot_pct = float(np.mean(bright_spots > 0))
        if spot_pct > 0.01 and spot_pct < 0.15:
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
            return 10, {"method": "wheel_closeup", "confidence": "high"}

        if b < 100 and ep < 14 and lap < 600:
            if ep < 10 and b < 85:
                return 10, {"method": "dark_very_smooth", "confidence": "medium"}
            if sat < 55 and red_pct > 0.02:
                return 9, {"method": "dark_red_objects", "confidence": "medium"}
            if white_pct > 0.15 and has_wheel:
                return 10, {"method": "dark_white_objects_wheel", "confidence": "medium"}
            if has_wheel:
                return 10, {"method": "dark_wheel_detected", "confidence": "medium"}
            return 9, {"method": "dark_smooth_indoor", "confidence": "medium"}
        if b < 115 and ep < 15 and lap < 700:
            if sat < 50:
                return 9, {"method": "carparts_default", "confidence": "low"}
            return 10, {"method": "carparts_saturated", "confidence": "low"}

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
