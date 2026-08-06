"""Unified evaluation runner for the photo classifier. Replaces the 10
ad-hoc test_*.py scripts (which either evaluated on the same data the
thresholds were tuned on, or destructively shutil.rmtree'd ref_train/ref_test
on every run).

Does not copy or delete any dataset directory. Groups images into
approximate photo sessions (eval/grouping.py) before splitting, so
near-duplicate consecutive shots can't leak across the split.

Usage (inside the backend container/image, where cv2/pytesseract are
available):
    python -m eval.evaluate --dataset fotos_prueba --mode classify
    python -m eval.evaluate --dataset fotos_prueba --mode batch
"""
import os
import sys
import json
import time
import argparse
from collections import defaultdict
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eval.grouping import group_by_session
from src.infrastructure.analysis.photo_classifier import PhotoClassifier, INSPECTION_POSITIONS


def make_classifier(name: str):
    if name == "heuristic":
        return PhotoClassifier()
    if name == "embedding":
        from src.infrastructure.analysis.embedding_classifier import EmbeddingPositionClassifier
        return EmbeddingPositionClassifier()
    raise ValueError(f"Unknown classifier: {name}")


def load_dataset(dataset_dir: str) -> list[tuple[str, int]]:
    """Returns list of (image_path, expected_position)."""
    items = []
    for folder in sorted(os.listdir(dataset_dir)):
        fpath = os.path.join(dataset_dir, folder)
        if not os.path.isdir(fpath):
            continue
        try:
            expected = int(folder.split(" -")[0])
        except ValueError:
            continue
        for img in sorted(os.listdir(fpath)):
            img_path = os.path.join(fpath, img)
            if os.path.isfile(img_path):
                items.append((img_path, expected))
    return items


def make_folds(items: list[tuple[str, int]]) -> tuple[list[int], int]:
    """Groups items by session and returns (group_id per item, n_groups)."""
    group_ids = group_by_session(items)
    n_groups = len(set(group_ids))
    return group_ids, n_groups


def evaluate_classify(items: list[tuple[str, int]], group_ids: list[int], classifier_name: str = "heuristic") -> dict:
    """Per-photo classify() accuracy under group-held-out protocol.

    The heuristic classifier isn't trained on data, so "holding out" a group
    doesn't change classifier behavior -- but it still defines the honest
    evaluation set and prevents conflating near-duplicate shots as
    independent samples in the reported per-position counts.

    The embedding classifier IS trained on data (see eval/train_head.py),
    so this number reuses whatever position_head.json is currently on disk
    -- it is only a true holdout number if that head was cross-validated
    (train_head.py's own leave-one-session-out CV), not re-validated here.
    """
    classifier = make_classifier(classifier_name)
    confusion = defaultdict(lambda: defaultdict(int))  # expected -> predicted(or "None") -> count
    method_counts = defaultdict(int)
    correct = 0
    unclassified = 0
    total = len(items)

    start = time.time()
    for (path, expected), _gid in zip(items, group_ids):
        pos, info = classifier.classify(path)
        confusion[expected][pos if pos is not None else "None"] += 1
        method_counts[info.get("method", "unknown")] += 1
        if pos is None:
            unclassified += 1
        elif pos == expected:
            correct += 1
    elapsed = time.time() - start

    per_position = {}
    for expected in sorted(confusion):
        total_pos = sum(confusion[expected].values())
        correct_pos = confusion[expected].get(expected, 0)
        per_position[expected] = {
            "label": INSPECTION_POSITIONS.get(expected, "?"),
            "correct": correct_pos,
            "total": total_pos,
            "accuracy": round(correct_pos / total_pos, 4) if total_pos else None,
        }

    return {
        "mode": "classify",
        "n_images": total,
        "n_groups": len(set(group_ids)),
        "accuracy": round(correct / total, 4) if total else None,
        "coverage": round(1 - unclassified / total, 4) if total else None,
        "elapsed_seconds": round(elapsed, 2),
        "per_position": per_position,
        "confusion_matrix": {str(k): dict(v) for k, v in confusion.items()},
        "method_breakdown": dict(method_counts),
    }


def evaluate_batch(items: list[tuple[str, int]], group_ids: list[int]) -> dict:
    """classify_batch() accuracy: groups items by session and runs the
    batch assignment (with collision resolution) within each session,
    which is closer to production usage than isolated classify() calls."""
    classifier = PhotoClassifier()
    by_group: dict[int, list[tuple[str, int]]] = defaultdict(list)
    for (path, expected), gid in zip(items, group_ids):
        by_group[gid].append((path, expected))

    confusion = defaultdict(lambda: defaultdict(int))
    correct = 0
    unassigned = 0
    total = 0

    start = time.time()
    for gid, group_items in by_group.items():
        paths = [p for p, _ in group_items]
        expected_by_path = dict(group_items)
        assignments = classifier.classify_batch(paths)
        for path, expected in group_items:
            total += 1
            pos = assignments.get(path, {}).get("position")
            confusion[expected][pos if pos is not None else "None"] += 1
            if pos is None:
                unassigned += 1
            elif pos == expected:
                correct += 1
    elapsed = time.time() - start

    per_position = {}
    for expected in sorted(confusion):
        total_pos = sum(confusion[expected].values())
        correct_pos = confusion[expected].get(expected, 0)
        per_position[expected] = {
            "label": INSPECTION_POSITIONS.get(expected, "?"),
            "correct": correct_pos,
            "total": total_pos,
            "accuracy": round(correct_pos / total_pos, 4) if total_pos else None,
        }

    return {
        "mode": "batch",
        "n_images": total,
        "n_groups": len(by_group),
        "accuracy": round(correct / total, 4) if total else None,
        "coverage": round(1 - unassigned / total, 4) if total else None,
        "elapsed_seconds": round(elapsed, 2),
        "per_position": per_position,
        "confusion_matrix": {str(k): dict(v) for k, v in confusion.items()},
    }


def print_report(result: dict) -> None:
    print(f"\n== {result['mode'].upper()} accuracy ==")
    print(f"images={result['n_images']} groups={result['n_groups']} "
          f"accuracy={result['accuracy']} coverage={result['coverage']} "
          f"elapsed={result['elapsed_seconds']}s")
    print("\nPer position:")
    for pos, d in result["per_position"].items():
        print(f"  {pos:>2} {d['label']:<28} {d['correct']}/{d['total']} ({d['accuracy']})")
    if result.get("method_breakdown"):
        print("\nMethod breakdown:")
        for method, count in sorted(result["method_breakdown"].items(), key=lambda x: -x[1]):
            print(f"  {method}: {count}")
    print("\nConfusion matrix (row=expected, col=predicted):")
    positions = sorted(INSPECTION_POSITIONS) + ["None"]
    header = "      " + " ".join(f"{p!s:>4}" for p in positions)
    print(header)
    for expected in sorted(INSPECTION_POSITIONS):
        row = result["confusion_matrix"].get(str(expected), {})
        line = f"exp{expected:>3} " + " ".join(f"{row.get(str(p), row.get(p, 0)):>4}" for p in positions)
        print(line)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="/app/fotos_prueba")
    parser.add_argument("--mode", choices=["classify", "batch", "both"], default="both")
    parser.add_argument("--classifier", choices=["heuristic", "embedding"], default="heuristic")
    parser.add_argument("--out", default=None)
    parser.add_argument("--no-ocr", action="store_true", help="Skip OCR text detection (faster, but positions 1/11 override never fires)")
    args = parser.parse_args()

    if args.no_ocr:
        os.environ["SKIP_OCR_DETECTION"] = "1"

    items = load_dataset(args.dataset)
    if not items:
        print(f"No images found under {args.dataset}", file=sys.stderr)
        sys.exit(1)

    group_ids, n_groups = make_folds(items)

    if args.classifier == "embedding" and args.mode in ("batch", "both"):
        print("NOTE: --classifier embedding only supports --mode classify "
              "(batch/collision assignment is heuristic-only until Fase 2).", file=sys.stderr)
        args.mode = "classify"

    results = {}
    if args.mode in ("classify", "both"):
        results["classify"] = evaluate_classify(items, group_ids, args.classifier)
        print_report(results["classify"])
    if args.mode in ("batch", "both"):
        results["batch"] = evaluate_batch(items, group_ids)
        print_report(results["batch"])

    if n_groups < 5:
        print(f"\nWARNING: only {n_groups} distinct photo sessions detected in "
              f"{args.dataset}. Session grouping degenerates toward one big "
              f"group; treat this accuracy as inflated / not a real holdout.",
              file=sys.stderr)

    out_path = args.out
    if out_path is None:
        os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"), exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "results", f"{stamp}-{args.classifier}.json"
        )
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {out_path}")
