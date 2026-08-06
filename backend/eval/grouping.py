"""Groups dataset images into approximate photo sessions, to prevent a
leave-one-out or k-fold split from putting near-duplicate consecutive shots
on both sides of the split (which would leak information and inflate the
reported accuracy).

Filenames follow WhatsApp's export convention:
  "WhatsApp Image 2026-07-23 at 5.22.02 PM (1).jpeg"
Two photos whose timestamps are within GROUP_WINDOW_SECONDS of each other
are treated as the same session/vehicle.
"""
import os
import re
from datetime import datetime, timedelta

GROUP_WINDOW_SECONDS = 90

_TIMESTAMP_RE = re.compile(
    r"(\d{4}-\d{2}-\d{2}) at (\d{1,2})\.(\d{2})\.(\d{2})\s*(AM|PM)", re.IGNORECASE
)


def parse_timestamp(filename: str) -> "datetime | None":
    m = _TIMESTAMP_RE.search(filename)
    if not m:
        return None
    date_str, hour, minute, second, ampm = m.groups()
    hour = int(hour) % 12
    if ampm.upper() == "PM":
        hour += 12
    try:
        return datetime.strptime(
            f"{date_str} {hour:02d}:{minute}:{second}", "%Y-%m-%d %H:%M:%S"
        )
    except ValueError:
        return None


def group_by_session(items: list[tuple[str, int]]) -> list[int]:
    """items: list of (filename, position). Returns a group_id per item,
    aligned by index. Falls back to one group per item (i.e. plain
    leave-one-out) for any file whose timestamp can't be parsed."""
    parsed = [(parse_timestamp(os.path.basename(fname)), fname) for fname, _ in items]

    order = sorted(range(len(items)), key=lambda i: (parsed[i][0] is None, parsed[i][0] or datetime.min))

    group_ids = [-1] * len(items)
    next_group = 0
    window = timedelta(seconds=GROUP_WINDOW_SECONDS)
    last_ts = None

    for i in order:
        ts, _ = parsed[i]
        if ts is None:
            group_ids[i] = next_group
            next_group += 1
            last_ts = None
            continue
        if last_ts is not None and ts - last_ts <= window:
            group_ids[i] = next_group - 1
        else:
            group_ids[i] = next_group
            next_group += 1
        last_ts = ts

    return group_ids
