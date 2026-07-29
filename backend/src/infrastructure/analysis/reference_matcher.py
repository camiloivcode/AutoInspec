import os
import re
import logging
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

MATCH_THRESHOLD = 0.55


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

    feats = {}

    feats["brightness"] = float(np.mean(gray))
    feats["color_std"] = float(np.std(img))
    edges = cv2.Canny(gray, 50, 150)
    feats["edge_pct"] = float(np.mean(edges > 0)) * 100
    feats["sat_mean"] = float(np.mean(hsv[:, :, 1]))
    feats["hue_mean"] = float(np.mean(hsv[:, :, 0]))
    feats["blue_ratio"] = float(np.mean(img[:, :, 0] > 150))
    feats["green_ratio"] = float(np.mean(img[:, :, 1] > 150))
    feats["laplacian_var"] = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    h_hist = cv2.calcHist([hsv], [0], None, [12], [0, 180]).flatten()
    feats["h_hist"] = (h_hist / (h_hist.sum() + 1e-6)).tolist()
    s_hist = cv2.calcHist([hsv], [1], None, [8], [0, 256]).flatten()
    feats["s_hist"] = (s_hist / (s_hist.sum() + 1e-6)).tolist()
    v_hist = cv2.calcHist([hsv], [2], None, [8], [0, 256]).flatten()
    feats["v_hist"] = (v_hist / (v_hist.sum() + 1e-6)).tolist()

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
    feats["edge_hist"] = (edge_hist / (edge_hist.sum() + 1e-6)).tolist()

    quad_feats = []
    for qy in range(3):
        for qx in range(3):
            y1, y2 = qy * h // 3, (qy + 1) * h // 3
            x1, x2 = qx * w // 3, (qx + 1) * w // 3
            quad = img[y1:y2, x1:x2]
            quad_gray = cv2.cvtColor(quad, cv2.COLOR_BGR2GRAY)
            quad_feats.append(float(np.mean(quad_gray)))
            quad_feats.append(float(np.std(quad_gray)))
    feats["quad_stats"] = quad_feats

    center = img[h // 4: 3 * h // 4, w // 4: 3 * w // 4]
    center_gray = cv2.cvtColor(center, cv2.COLOR_BGR2GRAY)
    feats["center_brightness"] = float(np.mean(center_gray))
    feats["center_std"] = float(np.std(center_gray))

    return feats


def _chi2_dist(h1: list, h2: list) -> float:
    a = np.array(h1, dtype=np.float64) + 1e-10
    b = np.array(h2, dtype=np.float64) + 1e-10
    return float(np.sum((a - b) ** 2 / (a + b + 1e-10)))


class ReferenceMatcher:
    def __init__(self, reference_dir: str = "/app/fotos_prueba"):
        self.centroids: dict[int, dict] = {}
        self.samples: dict[int, list[dict]] = {}
        self._load_references(reference_dir)

    def _load_references(self, directory: str):
        if not os.path.isdir(directory):
            logger.warning(f"Reference directory not found: {directory}")
            return

        all_features: dict[int, list[dict]] = {}

        for folder in sorted(os.listdir(directory)):
            folder_path = os.path.join(directory, folder)
            if not os.path.isdir(folder_path):
                continue
            match = re.match(r"(\d+)", folder)
            if not match:
                continue
            pos = int(match.group(1))
            if pos < 1 or pos > 11:
                continue

            for fname in sorted(os.listdir(folder_path)):
                path = os.path.join(folder_path, fname)
                if not os.path.isfile(path):
                    continue
                feats = extract_features(path)
                if feats:
                    all_features.setdefault(pos, []).append(feats)

        self.samples = all_features

        for pos, feat_list in all_features.items():
            centroid = self._compute_centroid(feat_list)
            self.centroids[pos] = centroid
            logger.info(f"Position {pos}: {len(feat_list)} samples")

        logger.info(f"Loaded {len(self.centroids)} positions, {sum(len(v) for v in self.samples.values())} total samples")

    def _distance_between(self, a: dict, b: dict) -> float:
        return self._distance_to_centroid(a, b)

    def knn_match(self, features: dict, k: int = 3) -> Optional[tuple[int, float]]:
        if not self.samples:
            return None

        all_dists: list[tuple[int, float]] = []
        for pos, sample_list in self.samples.items():
            for sample in sample_list:
                dist = self._distance_between(features, sample)
                all_dists.append((pos, dist))

        all_dists.sort(key=lambda x: x[1])
        top_k = all_dists[:k]

        weights: dict[int, float] = {}
        for pos, dist in top_k:
            w = 1.0 / (dist + 1e-6)
            weights[pos] = weights.get(pos, 0.0) + w

        if not weights:
            return None

        best_pos = max(weights, key=weights.get)
        avg_dist = sum(d for _, d in top_k) / k

        pos_weight = weights[best_pos]
        second_weight = max((w for p, w in weights.items() if p != best_pos), default=0)
        margin = (pos_weight - second_weight) / (pos_weight + 1e-6)

        if margin > 0.15:
            return best_pos, avg_dist
        return None

    def _compute_centroid(self, features: list[dict]) -> dict:
        centroid = {}
        scalar_keys = [
            "brightness", "color_std", "edge_pct", "sat_mean",
            "hue_mean", "blue_ratio", "green_ratio", "laplacian_var",
            "center_brightness", "center_std",
        ]
        for key in scalar_keys:
            vals = [f[key] for f in features if key in f]
            centroid[key] = float(np.mean(vals)) if vals else 0.0

        for hist_key in ["h_hist", "s_hist", "v_hist", "edge_hist"]:
            hists = [np.array(f[hist_key]) for f in features if hist_key in f]
            if hists:
                centroid[hist_key] = np.mean(hists, axis=0).tolist()
            else:
                centroid[hist_key] = []

        quad_lists = [np.array(f["quad_stats"]) for f in features if "quad_stats" in f]
        if quad_lists:
            centroid["quad_stats"] = np.mean(quad_lists, axis=0).tolist()
        else:
            centroid["quad_stats"] = []

        return centroid

    def _distance_to_centroid(self, features: dict, centroid: dict) -> float:
        scalar_dist = 0.0
        scalar_keys = [
            ("brightness", 0.06, 255.0),
            ("color_std", 0.06, 128.0),
            ("edge_pct", 0.10, 100.0),
            ("sat_mean", 0.06, 255.0),
            ("hue_mean", 0.03, 180.0),
            ("blue_ratio", 0.04, 1.0),
            ("green_ratio", 0.03, 1.0),
            ("laplacian_var", 0.10, 2000.0),
            ("center_brightness", 0.04, 255.0),
            ("center_std", 0.04, 128.0),
        ]
        for key, weight, norm in scalar_keys:
            diff = (features.get(key, 0.0) - centroid.get(key, 0.0)) / norm
            scalar_dist += weight * (diff * diff)

        hist_dist = 0.0
        for hist_key in ["h_hist", "s_hist", "v_hist", "edge_hist"]:
            fa = features.get(hist_key, [])
            ca = centroid.get(hist_key, [])
            if fa and ca:
                hist_dist += _chi2_dist(fa, ca) * 0.015

        quad_dist = 0.0
        fq = features.get("quad_stats", [])
        cq = centroid.get("quad_stats", [])
        if fq and cq and len(fq) == len(cq):
            arr_f = np.array(fq)
            arr_c = np.array(cq)
            max_vals = np.maximum(np.abs(arr_f), np.abs(arr_c))
            max_vals[max_vals < 1] = 1.0
            norm_diff = ((arr_f - arr_c) / max_vals) ** 2
            quad_dist = float(np.mean(norm_diff)) * 0.06

        total = scalar_dist + hist_dist + quad_dist
        return total ** 0.5

    def match(self, features: dict) -> Optional[tuple[int, float]]:
        if not self.centroids:
            return None

        best_pos = None
        best_dist = float("inf")

        for pos, centroid in self.centroids.items():
            dist = self._distance_to_centroid(features, centroid)
            if dist < best_dist:
                best_dist = dist
                best_pos = pos

        if best_pos is not None and best_dist <= MATCH_THRESHOLD:
            return best_pos, best_dist
        return None
