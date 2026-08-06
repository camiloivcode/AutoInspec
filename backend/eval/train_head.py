"""Offline training script for the CLIP-embedding position head
(position_head.json, consumed by embedding_classifier.EmbeddingPositionClassifier).

Dev-only: needs scikit-learn, which is NOT in requirements.txt (runtime
inference is numpy-only -- softmax(W @ embedding + b)). Run inside a
container that has it installed, e.g. the throwaway Dockerfile.eval image
used to build this feature:
    docker run --rm -v "$(pwd):/app" autoinspec-backend-eval-ml \
        python -m eval.train_head --dataset /app/fotos_prueba

Never applies horizontal flip augmentation: positions 4/5 (left/right side)
and 3/7 (three-quarter front/rear) are mirror-image pairs, so a flipped
photo would carry the wrong label and destroy exactly the distinction that
matters most.

Reports leave-one-session-out cross-validation accuracy (see
eval/grouping.py -- same session grouping evaluate.py uses, so the number is
comparable to the heuristic classifier's baseline) before fitting the final
head on all 81 photos.
"""
import os
import sys
import json
import argparse
import random

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eval.evaluate import load_dataset
from eval.grouping import group_by_session
from src.infrastructure.analysis.embedding_classifier import ClipEmbedder, preprocess_clip_array
from src.infrastructure.analysis.photo_classifier import INSPECTION_POSITIONS

AUGMENTATIONS_PER_IMAGE = 9  # + 1 original = 10x effective training data


def augment_bgr(img: np.ndarray, rng: random.Random) -> np.ndarray:
    """Brightness/contrast/saturation jitter + small rotation + random crop.
    No flip -- see module docstring."""
    h, w = img.shape[:2]

    angle = rng.uniform(-5, 5)
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    img = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT)

    crop_frac = rng.uniform(0.90, 1.0)
    ch, cw = int(h * crop_frac), int(w * crop_frac)
    top = rng.randint(0, h - ch) if h > ch else 0
    left = rng.randint(0, w - cw) if w > cw else 0
    img = img[top:top + ch, left:left + cw]

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] *= rng.uniform(0.7, 1.3)  # saturation
    hsv[:, :, 2] *= rng.uniform(0.75, 1.25)  # value/brightness
    hsv = np.clip(hsv, 0, 255).astype(np.uint8)
    img = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    contrast = rng.uniform(0.85, 1.15)
    img = np.clip((img.astype(np.float32) - 127.5) * contrast + 127.5, 0, 255).astype(np.uint8)

    quality = rng.randint(60, 95)
    ok, enc = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if ok:
        img = cv2.imdecode(enc, cv2.IMREAD_COLOR)

    return img


def embed_with_augmentations(embedder: ClipEmbedder, path: str, n_aug: int, rng: random.Random) -> list[np.ndarray]:
    img_bgr = cv2.imread(path)
    if img_bgr is None:
        return []
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    embeddings = [embedder.embed_array(preprocess_clip_array(img_rgb))]
    for _ in range(n_aug):
        aug_bgr = augment_bgr(img_bgr, rng)
        aug_rgb = cv2.cvtColor(aug_bgr, cv2.COLOR_BGR2RGB)
        embeddings.append(embedder.embed_array(preprocess_clip_array(aug_rgb)))
    return embeddings


def fit_head(X: np.ndarray, y: np.ndarray, positions: list[int]):
    from sklearn.linear_model import LogisticRegression
    clf = LogisticRegression(
        multi_class="multinomial", C=0.1, max_iter=2000, random_state=0,
    )
    clf.fit(X, y)
    # sklearn orders classes_ alphabetically/numerically; realign to `positions`.
    weights = np.zeros((len(positions), X.shape[1]), dtype=np.float64)
    bias = np.zeros(len(positions), dtype=np.float64)
    for i, cls in enumerate(clf.classes_):
        idx = positions.index(cls)
        weights[idx] = clf.coef_[i]
        bias[idx] = clf.intercept_[i]
    return weights, bias


def cross_validate(items, group_ids, embeddings_by_path, positions, seed) -> float:
    groups = sorted(set(group_ids))
    correct, total = 0, 0
    for held_out_group in groups:
        train_X, train_y = [], []
        for (path, pos), gid in zip(items, group_ids):
            if gid == held_out_group:
                continue
            for emb in embeddings_by_path[path]:
                train_X.append(emb)
                train_y.append(pos)
        if len(set(train_y)) < 2:
            continue
        weights, bias = fit_head(np.array(train_X), np.array(train_y), positions)

        for (path, expected), gid in zip(items, group_ids):
            if gid != held_out_group:
                continue
            base_emb = embeddings_by_path[path][0]  # unaugmented
            logits = weights @ base_emb + bias
            pred = positions[int(np.argmax(logits))]
            total += 1
            correct += int(pred == expected)
    return correct / total if total else 0.0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="/app/fotos_prueba")
    parser.add_argument("--out", default=None)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--skip-cv", action="store_true", help="Skip leave-one-session-out CV, just fit and export")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    items = load_dataset(args.dataset)
    if not items:
        print(f"No images found under {args.dataset}", file=sys.stderr)
        sys.exit(1)
    group_ids = group_by_session(items)
    positions = sorted(INSPECTION_POSITIONS.keys())

    print(f"Loaded {len(items)} images, {len(set(group_ids))} sessions. "
          f"Embedding with {AUGMENTATIONS_PER_IMAGE} augmentations each...")

    embedder = ClipEmbedder()
    embeddings_by_path: dict[str, list[np.ndarray]] = {}
    for i, (path, _pos) in enumerate(items):
        embeddings_by_path[path] = embed_with_augmentations(embedder, path, AUGMENTATIONS_PER_IMAGE, rng)
        if (i + 1) % 20 == 0:
            print(f"  embedded {i + 1}/{len(items)}")

    if not args.skip_cv:
        print("\nRunning leave-one-session-out cross-validation...")
        cv_acc = cross_validate(items, group_ids, embeddings_by_path, positions, args.seed)
        print(f"CV accuracy (held-out sessions, unaugmented eval images): {cv_acc:.4f}")

    print("\nFitting final head on all data...")
    all_X, all_y = [], []
    for path, pos in items:
        for emb in embeddings_by_path[path]:
            all_X.append(emb)
            all_y.append(pos)
    weights, bias = fit_head(np.array(all_X), np.array(all_y), positions)

    out_path = args.out or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "src", "infrastructure", "analysis", "position_head.json",
    )
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({
            "positions": positions,
            "weights": weights.tolist(),
            "bias": bias.tolist(),
        }, f)
    print(f"Wrote {out_path} ({weights.shape[0]}x{weights.shape[1]} weights)")
