"""Deterministic leave-N-out split of fotos_prueba into ref_train/ + ref_holdout/.

Both outputs keep the per-position folder structure (unlike the old flat,
unlabeled ref_test/), so per_pos.py can recover ground truth directly from
the folder name instead of an in-memory holdout map.

Usage: python split_dataset.py [--holdout-per-position 2] [--base /app]
"""
import os
import sys
import shutil
import argparse


def split(base: str, holdout_per_position: int) -> None:
    source = os.path.join(base, "fotos_prueba")
    train_dir = os.path.join(base, "ref_train")
    holdout_dir = os.path.join(base, "ref_holdout")

    for d in (train_dir, holdout_dir):
        if os.path.exists(d):
            shutil.rmtree(d)
        os.makedirs(d, exist_ok=True)

    for folder in sorted(os.listdir(source)):
        src = os.path.join(source, folder)
        if not os.path.isdir(src):
            continue

        images = sorted(f for f in os.listdir(src) if os.path.isfile(os.path.join(src, f)))
        n_holdout = min(holdout_per_position, max(0, len(images) - 1))

        train_images = images[:len(images) - n_holdout] if n_holdout else images
        holdout_images = images[len(images) - n_holdout:] if n_holdout else []

        dst_train = os.path.join(train_dir, folder)
        os.makedirs(dst_train, exist_ok=True)
        for img in train_images:
            shutil.copy2(os.path.join(src, img), os.path.join(dst_train, img))

        if holdout_images:
            dst_holdout = os.path.join(holdout_dir, folder)
            os.makedirs(dst_holdout, exist_ok=True)
            for img in holdout_images:
                shutil.copy2(os.path.join(src, img), os.path.join(dst_holdout, img))

        print(f"{folder}: {len(train_images)} train, {len(holdout_images)} holdout")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--holdout-per-position", type=int, default=2)
    parser.add_argument("--base", default="/app")
    args = parser.parse_args()
    split(args.base, args.holdout_per_position)
