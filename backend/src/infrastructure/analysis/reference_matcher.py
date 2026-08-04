import os
import re
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
    img_raw = cv2.imread(image_path)
    if img_raw is None:
        return None
    h, w, _ = img_raw.shape
    longest = max(h, w)
    if longest > MAX_ANALYSIS_PX:
        scale = MAX_ANALYSIS_PX / longest
        img_raw = cv2.resize(img_raw, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        h, w, _ = img_raw.shape

    img_norm = _normalize_image(img_raw)

    # Structure/sharpness features are kept on the raw image: CLAHE inflates
    # local contrast and would artificially raise laplacian_var/edge_pct,
    # defeating their use as blur/texture signals.
    gray_raw = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray_raw, 50, 150)
    edge_pct = float(np.mean(edges > 0)) * 100
    laplacian_var = float(cv2.Laplacian(gray_raw, cv2.CV_64F).var())
    color_std = float(np.std(img_raw))

    # Color/exposure features are computed on the normalized image so they
    # stop reflecting a single camera's white balance/exposure quirks.
    gray = cv2.cvtColor(img_norm, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(img_norm, cv2.COLOR_BGR2HSV)

    brightness = float(np.mean(gray))
    brightness_median = float(np.median(gray))
    brightness_mad = float(np.median(np.abs(gray.astype(np.float32) - brightness_median)))
    sat_mean = float(np.mean(hsv[:, :, 1]))
    sat_median = float(np.median(hsv[:, :, 1]))
    hue_mean = float(np.mean(hsv[:, :, 0]))
    blue_ratio = float(np.mean(img_norm[:, :, 0] > 150))
    green_ratio = float(np.mean(img_norm[:, :, 1] > 150))
    white_ratio = float(np.mean(gray > 220))

    center = img_norm[h // 4: 3 * h // 4, w // 4: 3 * w // 4]
    center_gray = cv2.cvtColor(center, cv2.COLOR_BGR2GRAY)
    center_brightness = float(np.mean(center_gray))
    center_std = float(np.std(center_gray))

    top_third = img_norm[:h // 3, :, :]
    top_gray = cv2.cvtColor(top_third, cv2.COLOR_BGR2GRAY)
    top_hsv = cv2.cvtColor(top_third, cv2.COLOR_BGR2HSV)
    sky_blue_ratio = float(np.mean(
        (top_hsv[:, :, 0] > 90) & (top_hsv[:, :, 0] < 130) &
        (top_hsv[:, :, 1] > 30) & (top_hsv[:, :, 2] > 80)
    ))
    top_bottom_brightness_ratio = float(np.mean(top_gray)) / (brightness + 1e-6)

    bottom_third = img_norm[2 * h // 3:, :, :]
    bottom_gray = cv2.cvtColor(bottom_third, cv2.COLOR_BGR2GRAY)
    bottom_brightness = float(np.mean(bottom_gray))

    return {
        "brightness": brightness,
        "brightness_median": brightness_median,
        "brightness_mad": brightness_mad,
        "color_std": color_std,
        "edge_pct": edge_pct,
        "sat_mean": sat_mean,
        "sat_median": sat_median,
        "hue_mean": hue_mean,
        "blue_ratio": blue_ratio,
        "green_ratio": green_ratio,
        "laplacian_var": laplacian_var,
        "white_ratio": white_ratio,
        "center_brightness": center_brightness,
        "center_std": center_std,
        "sky_blue_ratio": sky_blue_ratio,
        "top_bottom_brightness_ratio": top_bottom_brightness_ratio,
        "bottom_brightness": bottom_brightness,
        "orientation": "landscape" if w > h else "portrait",
        "aspect_ratio": round(w / h, 2),
    }
