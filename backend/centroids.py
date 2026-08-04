"""Prints per-position feature centroids from ref_train/, and (re)writes the
position_profiles.json artifact consumed by PhotoClassifier for collision
resolution (_find_alternative_position). Only ever reads ref_train/ — never
ref_holdout/, so the holdout set stays untouched by tuning.

Usage: python centroids.py [--base /app]
"""
import os
import sys
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.infrastructure.analysis.reference_matcher import extract_features
from src.infrastructure.analysis.photo_classifier import SIMILARITY_FEATURE_KEYS, DEFAULT_PROFILES_PATH
import numpy as np


def build(base: str) -> None:
    train_dir = os.path.join(base, "ref_train")

    all_features = {}
    for folder in sorted(os.listdir(train_dir)):
        fpath = os.path.join(train_dir, folder)
        if not os.path.isdir(fpath):
            continue
        pos = int(folder.split(" -")[0])
        for fname in sorted(os.listdir(fpath)):
            path = os.path.join(fpath, fname)
            if not os.path.isfile(path):
                continue
            feats = extract_features(path)
            if feats:
                all_features.setdefault(pos, []).append(feats)

    profiles = {}
    for pos in sorted(all_features.keys()):
        feats = all_features[pos]
        centroid = {k: float(np.mean([f[k] for f in feats])) for k in
                    ["brightness", "color_std", "edge_pct", "sat_mean", "hue_mean",
                     "blue_ratio", "green_ratio", "laplacian_var", "center_brightness", "center_std"]}
        print("Pos %2d: b=%5.0f cs=%5.0f ep=%5.1f%% sat=%5.0f hue=%5.0f bl=%4.2f gr=%4.2f lap=%5.0f cb=%5.0f cst=%5.0f  (n=%d)" % (
            pos, centroid["brightness"], centroid["color_std"], centroid["edge_pct"],
            centroid["sat_mean"], centroid["hue_mean"], centroid["blue_ratio"],
            centroid["green_ratio"], centroid["laplacian_var"],
            centroid["center_brightness"], centroid["center_std"],
            len(feats)))

        profiles[pos] = [float(np.mean([f[k] for f in feats])) for k in SIMILARITY_FEATURE_KEYS]

    with open(DEFAULT_PROFILES_PATH, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2)
    print(f"\nWrote {len(profiles)} position profiles to {DEFAULT_PROFILES_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="/app")
    args = parser.parse_args()
    build(args.base)
