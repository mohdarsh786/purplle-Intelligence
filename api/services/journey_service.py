"""
Journey Analytics Service -- Task 4.5

Computes customer journey paths from the SQLite events table.
Each journey is a single store visit (entry to exit) per track_id.

A journey ENDS when a person_exited event occurs.
After exit, a new journey begins on the next person_entered event.
This prevents recycled track_ids from creating infinite looping paths.

Outputs (per TASKS.md Task 4.5):
    - Top 5 customer paths (ordered zone sequences per visit)
    - Path frequency count
    - Average journey duration (per completed visit)

Data source:
    events table via api.db.sqlite helpers
"""

import logging
from collections import Counter
from datetime import datetime
from typing import Any

from api.db.sqlite import fetchall_as_dict

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("journey_service")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_DISPLAY_STEPS = 10

# Event types that represent zone transitions
_JOURNEY_EVENT_TYPES = {
    "person_entered",
    "zone_dwell_start",
    "queue_detected",
    "person_exited",
}

# ISO-8601 timestamp format used by the detector
_TS_FMT = "%Y-%m-%dT%H:%M:%SZ"


# ---------------------------------------------------------------------------
# Session Splitting
# ---------------------------------------------------------------------------


def _split_into_sessions(events: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """
    Split a track's chronological events into individual store visits.

    A session starts with any event and ends when a person_exited event
    is encountered. Events after the exit begin a new session.

    Returns:
        List of sessions, where each session is a list of event dicts.
    """
    sessions: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []

    for evt in events:
        current.append(evt)
        if evt["event_type"] == "person_exited":
            sessions.append(current)
            current = []

    # Any trailing events without a final exit form an incomplete session
    if current:
        sessions.append(current)

    return sessions


# ---------------------------------------------------------------------------
# Core Journey Logic
# ---------------------------------------------------------------------------


def _build_all_sessions() -> list[list[dict[str, Any]]]:
    """
    Query all journey-relevant events, group by track_id,
    then split each track into individual visit sessions.

    Returns:
        List of sessions (each session is a list of event dicts).
    """
    placeholders = ",".join("?" for _ in _JOURNEY_EVENT_TYPES)
    rows = fetchall_as_dict(
        f"""
        SELECT track_id, zone, timestamp, event_type
        FROM events
        WHERE event_type IN ({placeholders})
        ORDER BY track_id, timestamp, frame_no
        """,
        tuple(_JOURNEY_EVENT_TYPES),
    )

    # Group by track_id first
    tracks: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        tid = row["track_id"]
        if tid not in tracks:
            tracks[tid] = []
        tracks[tid].append(row)

    # Split each track into individual sessions
    all_sessions: list[list[dict[str, Any]]] = []
    for tid, events in tracks.items():
        sessions = _split_into_sessions(events)
        all_sessions.extend(sessions)

    return all_sessions


def _extract_zone_path(events: list[dict[str, Any]]) -> list[str]:
    """
    Extract an ordered, deduplicated zone path from a session's events.

    Consecutive duplicate zones are collapsed so
    [entry_zone, entry_zone, minimalist, minimalist, checkout_zone]
    becomes [entry_zone, minimalist, checkout_zone].

    Capped at MAX_DISPLAY_STEPS to prevent excessively long paths.
    """
    path: list[str] = []
    for evt in events:
        zone = evt["zone"]
        if not path or path[-1] != zone:
            if len(path) >= MAX_DISPLAY_STEPS:
                break
            path.append(zone)
    return path


def _compute_session_duration(session: list[dict[str, Any]]) -> float | None:
    """
    Compute journey duration for a single session (entry to exit).

    Returns duration in seconds, or None if fewer than 2 events
    or timestamps cannot be parsed.
    """
    if len(session) < 2:
        return None

    first_ts = session[0]["timestamp"]
    last_ts = session[-1]["timestamp"]

    try:
        t_start = datetime.strptime(first_ts, _TS_FMT)
        t_end = datetime.strptime(last_ts, _TS_FMT)
        delta = (t_end - t_start).total_seconds()
        return max(0.0, delta)
    except (ValueError, TypeError):
        logger.warning("Could not parse timestamps: %s -> %s", first_ts, last_ts)
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_top_paths(limit: int = 5) -> list[dict[str, Any]]:
    """
    Return the top N most common customer journey paths.

    Each path is an ordered list of zone names from a single store visit.
    Paths are ranked by frequency (how many visits followed that path).

    Returns:
        [
            {"path": ["entry_zone", "minimalist", "checkout_zone"], "count": 14},
            ...
        ]
    """
    sessions = _build_all_sessions()

    path_counter: Counter[tuple[str, ...]] = Counter()
    for session in sessions:
        path = _extract_zone_path(session)
        if len(path) >= 2:  # need at least 2 zones for a meaningful journey
            path_counter[tuple(path)] += 1

    top = path_counter.most_common(limit)
    results = [{"path": list(p), "count": c} for p, c in top]

    logger.info(
        "Journey paths computed -- %d sessions, %d unique paths, returning top %d",
        len(sessions), len(path_counter), limit,
    )
    return results


def get_average_journey_duration() -> float | None:
    """
    Compute the average journey duration across all completed visits.

    A completed visit is a session that ends with person_exited.
    Duration = last event timestamp - first event timestamp for each session.

    Returns duration in seconds, or None if no complete journeys exist.
    """
    sessions = _build_all_sessions()

    durations: list[float] = []
    for session in sessions:
        # Only count completed sessions (ending with person_exited)
        if not session or session[-1]["event_type"] != "person_exited":
            continue
        dur = _compute_session_duration(session)
        if dur is not None and dur > 0:
            durations.append(dur)

    if not durations:
        return None

    avg = round(sum(durations) / len(durations), 2)
    logger.info("Average journey duration: %.2fs across %d completed visits", avg, len(durations))
    return avg


def get_journey_data() -> dict[str, Any]:
    """
    Return the full journey response matching API_SPEC.md shape.

    Returns:
        {
            "top_paths": [...],
            "average_journey_duration_seconds": float|null
        }
    """
    return {
        "top_paths": get_top_paths(limit=5),
        "average_journey_duration_seconds": get_average_journey_duration(),
    }
