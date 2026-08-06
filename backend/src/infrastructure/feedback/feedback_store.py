import os
import json
import shutil
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

FEEDBACK_DIR = "/data/feedback"
LABELS_FILE = os.path.join(FEEDBACK_DIR, "labels.jsonl")


def record_batch(
    session_id: str,
    image_paths: list[str],
    suggested_positions: list[int | None],
    corrected_positions: list[int],
    confidences: list[str | None],
    methods: list[str | None],
) -> None:
    """Persists one (suggested, corrected) label pair per photo, plus a copy
    of the photo itself, before the caller's work_dir is deleted. This is
    the only source of human-verified labels on real (non-tuning-set)
    photos -- every other classifier signal in the app is discarded once
    the request finishes.
    """
    try:
        os.makedirs(FEEDBACK_DIR, exist_ok=True)
        session_dir = os.path.join(FEEDBACK_DIR, session_id)
        os.makedirs(session_dir, exist_ok=True)

        now = datetime.now(timezone.utc).isoformat()
        lines = []
        for path, suggested, corrected, confidence, method in zip(
            image_paths, suggested_positions, corrected_positions, confidences, methods
        ):
            if not os.path.exists(path):
                continue
            stored_name = f"{corrected}_{os.path.basename(path)}"
            shutil.copy2(path, os.path.join(session_dir, stored_name))
            lines.append(json.dumps({
                "session_id": session_id,
                "filename": stored_name,
                "suggested_position": suggested,
                "corrected_position": corrected,
                "confidence": confidence,
                "method": method,
                "timestamp": now,
            }, ensure_ascii=False))

        if lines:
            with open(LABELS_FILE, "a", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
    except Exception as e:
        logger.warning(f"Failed to record feedback batch for session {session_id}: {e}")
