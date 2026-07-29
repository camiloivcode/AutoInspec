import re
import logging
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import cv2
import pytesseract

logger = logging.getLogger(__name__)

COL_PLATE_PATTERN = re.compile(
    r"(?:(?:[A-Za-z]{3}[-.\s]?\d{3})|(?:[A-Za-z]{3}[-.\s]?\d{2}[A-Za-z]))"
)


class PlateDetector:
    def __init__(self, confidence_threshold: int = 40):
        self._threshold = confidence_threshold

    def detect_from_image(self, image_path: str) -> Optional[str]:
        try:
            img = cv2.imread(image_path)
            if img is None:
                return None
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LINEAR)
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            data = pytesseract.image_to_data(thresh, lang="spa", config="--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", output_type=pytesseract.Output.DICT)

            candidates = []
            for i in range(len(data["text"])):
                text = data["text"][i].strip()
                conf = int(data["conf"][i])
                if not text or conf < self._threshold:
                    continue
                cleaned = re.sub(r"[^A-Za-z0-9]", "", text).upper()
                if len(cleaned) < 5 or len(cleaned) > 8:
                    continue
                if not re.search(r"\d", cleaned) or not re.search(r"[A-Z]", cleaned):
                    continue
                match = COL_PLATE_PATTERN.search(cleaned)
                if match:
                    cleaned = match.group(0)
                candidates.append((cleaned, conf))

            data2 = pytesseract.image_to_data(gray, lang="spa", config="--psm 7", output_type=pytesseract.Output.DICT)
            for i in range(len(data2["text"])):
                text = data2["text"][i].strip()
                conf = int(data2["conf"][i])
                if not text or conf < self._threshold:
                    continue
                already = any(c[0] == re.sub(r"[^A-Z0-9]", "", text).upper() for c in candidates)
                if already:
                    continue
                cleaned = re.sub(r"[^A-Za-z0-9]", "", text).upper()
                if 5 <= len(cleaned) <= 8 and re.search(r"\d", cleaned) and re.search(r"[A-Z]", cleaned):
                    candidates.append((cleaned, conf))

            if candidates:
                candidates.sort(key=lambda x: x[1], reverse=True)
                logger.info(f"Plate candidates: {candidates}")
                return candidates[0][0]

        except Exception as e:
            logger.warning(f"OCR error on {image_path}: {e}")

        return None

    def detect_from_multiple(self, image_paths: list[str]) -> Optional[str]:
        best_plate = None
        best_confidence = 0

        for path in image_paths:
            plate = self.detect_from_image(path)
            if plate:
                if best_plate is None:
                    best_plate = plate
                    best_confidence = 80
                else:
                    if len(plate) == 7 and plate[:3].isalpha() and plate[3:].isdigit():
                        best_plate = plate
                        break

        return best_plate

    def detect_from_multiple_parallel(self, image_paths: list[str]) -> Optional[str]:
        best_plate = None
        best_score = 0
        n = len(image_paths)

        with ThreadPoolExecutor(max_workers=min(8, n)) as executor:
            fut_map = {executor.submit(self.detect_from_image, path): path for path in image_paths}
            for fut in as_completed(fut_map):
                path = fut_map[fut]
                try:
                    plate = fut.result()
                    if plate:
                        score = 0
                        if len(plate) == 7 and plate[:3].isalpha() and plate[3:].isdigit():
                            score = 100
                            best_plate = plate
                            break
                        score = len(plate)
                        if score > best_score:
                            best_score = score
                            best_plate = plate
                except Exception as e:
                    logger.debug(f"Plate detect failed for {path}: {e}")

        return best_plate
