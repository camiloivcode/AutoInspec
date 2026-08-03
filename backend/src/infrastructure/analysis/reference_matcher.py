import os
import re
import logging
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

MAX_ANALYSIS_PX = 800


def extract_features(image_path: str) -> Optional[dict]:
    img = cv2.imread(image_path)
    if img is None:
        return None
    h, w, _ = img.shape
    longest = max(h, w)
    if longest > MAX_ANALYSIS_PX:
        scale = MAX_ANALYSIS_PX / longest
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        h, w, _ = img.shape

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    brightness = float(np.mean(gray))
    color_std = float(np.std(img))
    edges = cv2.Canny(gray, 50, 150)
    edge_pct = float(np.mean(edges > 0)) * 100
    sat_mean = float(np.mean(hsv[:, :, 1]))
    hue_mean = float(np.mean(hsv[:, :, 0]))
    blue_ratio = float(np.mean(img[:, :, 0] > 150))
    green_ratio = float(np.mean(img[:, :, 1] > 150))
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    white_ratio = float(np.mean(gray > 220))

    center = img[h // 4: 3 * h // 4, w // 4: 3 * w // 4]
    center_gray = cv2.cvtColor(center, cv2.COLOR_BGR2GRAY)
    center_brightness = float(np.mean(center_gray))
    center_std = float(np.std(center_gray))

    top_third = img[:h // 3, :, :]
    top_gray = cv2.cvtColor(top_third, cv2.COLOR_BGR2GRAY)
    top_hsv = cv2.cvtColor(top_third, cv2.COLOR_BGR2HSV)
    sky_blue_ratio = float(np.mean(
        (top_hsv[:, :, 0] > 90) & (top_hsv[:, :, 0] < 130) &
        (top_hsv[:, :, 1] > 30) & (top_hsv[:, :, 2] > 80)
    ))

    bottom_third = img[2 * h // 3:, :, :]
    bottom_gray = cv2.cvtColor(bottom_third, cv2.COLOR_BGR2GRAY)
    bottom_brightness = float(np.mean(bottom_gray))

    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    mag = np.sqrt(sobelx**2 + sobely**2)
    angle = np.arctan2(sobely, sobelx + 1e-6)
    angle = np.mod(angle, np.pi)
    bin_size = np.pi / 9
    edge_hist = np.zeros(9)
    for b in range(9):
        mask = (angle >= b * bin_size) & (angle < (b + 1) * bin_size)
        edge_hist[b] = np.sum(mag[mask])
    edge_hist = (edge_hist / (edge_hist.sum() + 1e-6)).tolist()

    quad_feats = []
    for qy in range(3):
        for qx in range(3):
            y1, y2 = qy * h // 3, (qy + 1) * h // 3
            x1, x2 = qx * w // 3, (qx + 1) * w // 3
            quad = img[y1:y2, x1:x2]
            quad_gray = cv2.cvtColor(quad, cv2.COLOR_BGR2GRAY)
            quad_feats.append(float(np.mean(quad_gray)))
            quad_feats.append(float(np.std(quad_gray)))

    return {
        "brightness": brightness,
        "color_std": color_std,
        "edge_pct": edge_pct,
        "sat_mean": sat_mean,
        "hue_mean": hue_mean,
        "blue_ratio": blue_ratio,
        "green_ratio": green_ratio,
        "laplacian_var": laplacian_var,
        "white_ratio": white_ratio,
        "center_brightness": center_brightness,
        "center_std": center_std,
        "sky_blue_ratio": sky_blue_ratio,
        "bottom_brightness": bottom_brightness,
        "orientation": "landscape" if w > h else "portrait",
        "aspect_ratio": round(w / h, 2),
        "edge_hist": edge_hist,
        "quad_stats": quad_feats,
    }
