"""Per-position accuracy report for the photo classifier, run against
ref_train/ and/or ref_holdout/ (see split_dataset.py). Reports a
"generalization gap" (train_acc - holdout_acc) per position so a threshold
change that overfits ref_train shows up immediately as a growing gap.

Usage: python per_pos.py [--dataset train|holdout|both] [--base /app]
"""
import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.infrastructure.analysis.photo_classifier import PhotoClassifier, INSPECTION_POSITIONS


def run(dataset_dir: str, classifier: PhotoClassifier) -> dict:
    per_pos = {}
    if not os.path.isdir(dataset_dir):
        return per_pos

    for folder in sorted(os.listdir(dataset_dir)):
        fpath = os.path.join(dataset_dir, folder)
        if not os.path.isdir(fpath):
            continue
        expected = int(folder.split(" -")[0])
        correct = 0
        total = 0
        for img in sorted(os.listdir(fpath)):
            path = os.path.join(fpath, img)
            if not os.path.isfile(path):
                continue
            pos, info = classifier.classify(path)
            total += 1
            if pos == expected:
                correct += 1
        if total:
            per_pos[expected] = (correct, total)
    return per_pos


def print_table(title: str, per_pos: dict) -> None:
    print(f"\n== {title} ==")
    for pos in sorted(per_pos):
        c, t = per_pos[pos]
        print("Pos %2d (%s): %d/%d (%d%%)" % (pos, INSPECTION_POSITIONS[pos], c, t, c * 100 // t))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=["train", "holdout", "both"], default="both")
    parser.add_argument("--base", default="/app")
    args = parser.parse_args()

    c = PhotoClassifier()

    train_results, holdout_results = {}, {}
    if args.dataset in ("train", "both"):
        train_results = run(os.path.join(args.base, "ref_train"), c)
        print_table("TRAIN", train_results)
    if args.dataset in ("holdout", "both"):
        holdout_results = run(os.path.join(args.base, "ref_holdout"), c)
        print_table("HOLDOUT", holdout_results)

    if train_results and holdout_results:
        print("\n== GENERALIZATION GAP (train_acc - holdout_acc) ==")
        for pos in sorted(set(train_results) | set(holdout_results)):
            train_acc = (train_results[pos][0] * 100 // train_results[pos][1]) if pos in train_results else None
            holdout_acc = (holdout_results[pos][0] * 100 // holdout_results[pos][1]) if pos in holdout_results else None
            if train_acc is None or holdout_acc is None:
                continue
            gap = train_acc - holdout_acc
            flag = "  <-- overfitting?" if gap >= 20 else ""
            print("Pos %2d (%s): train=%d%% holdout=%d%% gap=%d%%%s" % (
                pos, INSPECTION_POSITIONS[pos], train_acc, holdout_acc, gap, flag))
