import logging
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

MAX_ANALYSIS_PX = 800


def _normalize_image(img: np.ndarray) -> np.ndarray:
    """Gray-world white balance + CLAHE, to make color/exposure features
    invariant to camera/lighting differences instead of comparing raw
    pixel values against thresholds tuned on one photo session."""
    b, g, r = cv2.split(img.astype(np.float32))
    overall_mean = (b.mean() + g.mean() + r.mean()) / 3.0
    for channel in (b, g, r):
        channel_mean = channel.mean()
        if channel_mean > 1e-3:
            channel *= overall_mean / channel_mean
    balanced = cv2.merge([b, g, r])
    balanced = np.clip(balanced, 0, 255).astype(np.uint8)

    lab = cv2.cvtColor(balanced, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_channel = clahe.apply(l_channel)
    lab = cv2.merge([l_channel, a_channel, b_channel])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def extract_features(image_path: str) -> Optional[dict]:
    """Only computes what photo_classifier.py's OCR override actually reads
    (brightness, brightness_median, white_ratio) -- this used to compute 19
    features for a hand-tuned threshold cascade that has since been replaced
    by the CLIP embedding classifier (see embedding_classifier.py)."""
    img_raw = cv2.imread(image_path)
    if img_raw is None:
        return None
    h, w, _ = img_raw.shape
    longest = max(h, w)
    if longest > MAX_ANALYSIS_PX:
        scale = MAX_ANALYSIS_PX / longest
        img_raw = cv2.resize(img_raw, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

    # Computed on the normalized image so brightness/white_ratio don't just
    # reflect a single camera's white balance/exposure quirks.
    img_norm = _normalize_image(img_raw)
    gray = cv2.cvtColor(img_norm, cv2.COLOR_BGR2GRAY)

    brightness = float(np.mean(gray))
    brightness_median = float(np.median(gray))
    white_ratio = float(np.mean(gray > 220))

    return {
        "brightness": brightness,
        "brightness_median": brightness_median,
        "white_ratio": white_ratio,
    }
