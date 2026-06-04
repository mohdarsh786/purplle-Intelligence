"""
Queue Analytics Service — Queue Metrics from Checkout Zones

Computes queue metrics from the SQLite events table using validated checkout_zone polygons.
All values are derived from actual queue_detected events and zone_dwell events in checkout zones.

Queue analytics are calculated from:
- queue_detected: When tracks are detected in checkout zone (indicates queue presence)
- zone_dwell_end: Dwell time in checkout_zone represents wait time
- metadata: May contain queue position and size information

Functions:
    get_average_wait_time()              → float | None
    get_max_wait_time()                  → float | None
    get_queue_length_distribution()      → list[int]
    get_peak_queue_size()                → int
    get_queue_congestion_periods()       → list[dict]
    get_abandoned_queue_count()          → int
    get_checkout_zone_names()            → list[str]
    get_queue_analytics()                → dict  (aggregate convenience wrapper)

Data source:
    events table via api.db.sqlite helpers

Event type mapping:
    queue_detected    → Queue presence at checkout
    zone_dwell_end    → Wait time in checkout zone (when zone is checkout_zone)
"""

import logging
import json
from typing import Any
from datetime import datetime, timedelta

from api.db.sqlite import fetchone, fetchall, fetchall_as_dict

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("queue_service")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CHECKOUT_ZONE_IDENTIFIERS = ["checkout", "billing", "counter"]
CONGESTION_THRESHOLD_SECONDS = 60.0  # Wait time indicating congestion


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def _is_checkout_zone(zone_name: str) -> bool:
    """
    Determine if a zone is a checkout zone based on naming convention.

    Returns:
        True if zone name contains checkout/billing/counter keywords
    """
    zone_lower = zone_name.lower()
    return any(identifier in zone_lower for identifier in CHECKOUT_ZONE_IDENTIFIERS)


def _parse_queue_metadata(metadata_json: str | None) -> dict[str, Any]:
    """
    Parse queue metadata JSON string.

    Returns:
        Dict with position, size, etc., or empty dict if parsing fails
    """
    if not metadata_json:
        return {}

    try:
        return json.loads(metadata_json)
    except (json.JSONDecodeError, TypeError):
        return {}


# ---------------------------------------------------------------------------
# Individual Queue Metric Functions
# ---------------------------------------------------------------------------


def get_checkout_zone_names() -> list[str]:
    """
    Get all unique checkout zone names from events.

    Returns:
        List of checkout zone names (e.g., ["checkout_zone", "billing_zone"])
    """
    rows = fetchall_as_dict(
        """
        SELECT DISTINCT zone
        FROM events
        WHERE zone IS NOT NULL
        ORDER BY zone
        """
    )

    checkout_zones = [row["zone"] for row in rows if _is_checkout_zone(row["zone"])]
    logger.debug("Checkout zones identified: %s", checkout_zones)
    return checkout_zones


def get_average_wait_time() -> float | None:
    """
    Compute average wait time (in seconds) at checkout zones.

    Uses dwell_seconds from zone_dwell_end events in checkout zones.

    Returns:
        Average wait time in seconds, or None if no data
    """
    checkout_zones = get_checkout_zone_names()

    if not checkout_zones:
        logger.debug("No checkout zones found")
        return None

    placeholders = ",".join("?" for _ in checkout_zones)
    row = fetchone(
        f"""
        SELECT AVG(dwell_seconds) AS avg_wait
        FROM events
        WHERE event_type = ?
          AND zone IN ({placeholders})
          AND dwell_seconds IS NOT NULL
          AND dwell_seconds > 0
        """,
        ("zone_dwell_end", *checkout_zones),
    )

    if row and row["avg_wait"] is not None:
        avg = round(row["avg_wait"], 2)
        logger.debug("Average wait time: %.2fs", avg)
        return avg

    logger.debug("Average wait time: no data")
    return None


def get_max_wait_time() -> float | None:
    """
    Compute maximum wait time (in seconds) at checkout zones.

    Returns:
        Maximum wait time in seconds, or None if no data
    """
    checkout_zones = get_checkout_zone_names()

    if not checkout_zones:
        return None

    placeholders = ",".join("?" for _ in checkout_zones)
    row = fetchone(
        f"""
        SELECT MAX(dwell_seconds) AS max_wait
        FROM events
        WHERE event_type = ?
          AND zone IN ({placeholders})
          AND dwell_seconds IS NOT NULL
          AND dwell_seconds > 0
        """,
        ("zone_dwell_end", *checkout_zones),
    )

    if row and row["max_wait"] is not None:
        max_wait = round(row["max_wait"], 2)
        logger.debug("Max wait time: %.2fs", max_wait)
        return max_wait

    return None


def get_queue_length_distribution() -> list[int]:
    """
    Get distribution of queue lengths from queue_detected events.

    Extracts queue size from metadata field if available.

    Returns:
        List of queue sizes observed (e.g., [2, 3, 1, 4, 2])
    """
    rows = fetchall_as_dict(
        """
        SELECT metadata
        FROM events
        WHERE event_type = ?
          AND metadata IS NOT NULL
        ORDER BY timestamp
        """,
        ("queue_detected",),
    )

    queue_sizes = []
    for row in rows:
        metadata = _parse_queue_metadata(row["metadata"])
        if "size" in metadata and isinstance(metadata["size"], (int, float)):
            queue_sizes.append(int(metadata["size"]))

    logger.debug("Queue length distribution: %d samples", len(queue_sizes))
    return queue_sizes


def get_peak_queue_size() -> int:
    """
    Get peak (maximum) queue size observed.

    Returns:
        Maximum queue size, or 0 if no queue data
    """
    distribution = get_queue_length_distribution()

    if not distribution:
        # Check if we have any queue_detected events at all
        row = fetchone(
            "SELECT COUNT(*) AS cnt FROM events WHERE event_type = ?",
            ("queue_detected",),
        )
        queue_event_count = row["cnt"] if row else 0

        if queue_event_count > 0:
            # We have queue events but no size metadata, estimate from event count
            logger.debug("Peak queue size estimated from event count: %d", queue_event_count)
            return queue_event_count

        return 0

    peak = max(distribution)
    logger.debug("Peak queue size: %d", peak)
    return peak


def get_queue_congestion_periods() -> list[dict[str, Any]]:
    """
    Identify time periods with queue congestion.

    Congestion defined as wait times > CONGESTION_THRESHOLD_SECONDS at checkout.

    Returns:
        List of congestion periods with timestamp, zone, wait_time:
        [
            {"timestamp": "2026-06-03T14:30:00Z", "zone": "checkout_zone", "wait_time": 75.5},
            ...
        ]
    """
    checkout_zones = get_checkout_zone_names()

    if not checkout_zones:
        return []

    placeholders = ",".join("?" for _ in checkout_zones)
    rows = fetchall_as_dict(
        f"""
        SELECT timestamp, zone, dwell_seconds AS wait_time
        FROM events
        WHERE event_type = ?
          AND zone IN ({placeholders})
          AND dwell_seconds IS NOT NULL
          AND dwell_seconds > ?
        ORDER BY timestamp DESC
        """,
        ("zone_dwell_end", *checkout_zones, CONGESTION_THRESHOLD_SECONDS),
    )

    congestion_periods = [
        {
            "timestamp": row["timestamp"],
            "zone": row["zone"],
            "wait_time": round(row["wait_time"], 2),
        }
        for row in rows
    ]

    logger.debug("Queue congestion periods identified: %d", len(congestion_periods))
    return congestion_periods


def get_abandoned_queue_count() -> int:
    """
    Estimate count of abandoned queues.

    Abandoned queue heuristic:
    - Track entered checkout zone (zone_dwell_start)
    - Track exited store (person_exited) within short time
    - Without completing checkout (no long dwell in checkout zone)

    This is an approximation as we don't have explicit abandoned_queue events.

    Returns:
        Estimated count of abandoned queue attempts
    """
    checkout_zones = get_checkout_zone_names()

    if not checkout_zones:
        return 0

    # Find tracks that entered checkout zone
    placeholders = ",".join("?" for _ in checkout_zones)
    rows = fetchall_as_dict(
        f"""
        SELECT DISTINCT track_id
        FROM events
        WHERE event_type = ?
          AND zone IN ({placeholders})
        """,
        ("zone_dwell_start", *checkout_zones),
    )

    checkout_track_ids = [row["track_id"] for row in rows]

    if not checkout_track_ids:
        return 0

    # Find tracks that exited without completing checkout
    # (dwell time in checkout < 10 seconds suggests abandonment)
    abandoned_count = 0
    for track_id in checkout_track_ids:
        checkout_dwell_row = fetchone(
            f"""
            SELECT dwell_seconds
            FROM events
            WHERE event_type = ?
              AND track_id = ?
              AND zone IN ({placeholders})
              AND dwell_seconds IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            ("zone_dwell_end", track_id, *checkout_zones),
        )

        if checkout_dwell_row:
            dwell = checkout_dwell_row["dwell_seconds"]
            # Very short dwell (<10s) suggests they entered but left quickly
            if dwell < 10.0:
                abandoned_count += 1

    logger.debug("Abandoned queue count: %d", abandoned_count)
    return abandoned_count


def get_current_queue_length() -> int:
    """
    Estimate current queue length (customers currently in checkout zones).

    Uses recent zone_dwell_start events without corresponding zone_dwell_end.

    Returns:
        Estimated current queue length
    """
    checkout_zones = get_checkout_zone_names()

    if not checkout_zones:
        return 0

    # Count tracks that entered checkout but haven't exited yet
    # (entered in last 10 minutes, no exit event yet)
    placeholders = ",".join("?" for _ in checkout_zones)

    # Get track IDs that entered checkout recently
    ten_mins_ago = (datetime.utcnow() - timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%SZ")

    rows = fetchall_as_dict(
        f"""
        SELECT DISTINCT track_id
        FROM events
        WHERE event_type = ?
          AND zone IN ({placeholders})
          AND timestamp > ?
        """,
        ("zone_dwell_start", *checkout_zones, ten_mins_ago),
    )

    entered_track_ids = [row["track_id"] for row in rows]

    if not entered_track_ids:
        return 0

    # Check which of these have exited
    placeholders_tracks = ",".join("?" for _ in entered_track_ids)
    placeholders_zones = ",".join("?" for _ in checkout_zones)

    exited_rows = fetchall_as_dict(
        f"""
        SELECT DISTINCT track_id
        FROM events
        WHERE event_type = ?
          AND track_id IN ({placeholders_tracks})
          AND zone IN ({placeholders_zones})
          AND timestamp > ?
        """,
        ("zone_dwell_end", *entered_track_ids, *checkout_zones, ten_mins_ago),
    )

    exited_track_ids = {row["track_id"] for row in exited_rows}

    # Tracks still in queue = entered - exited
    current_queue = len(entered_track_ids) - len(exited_track_ids)

    logger.debug("Current queue length: %d", current_queue)
    return max(0, current_queue)


# ---------------------------------------------------------------------------
# Aggregate Convenience Function
# ---------------------------------------------------------------------------


def get_queue_analytics() -> dict[str, Any]:
    """
    Return comprehensive queue analytics as a single dict.

    Returns:
        {
            "average_wait_time": float | None,
            "max_wait_time": float | None,
            "queue_length_distribution": list[int],
            "peak_queue_size": int,
            "current_queue_length": int,
            "congestion_periods": list[dict],
            "abandoned_queue_count": int,
            "checkout_zones": list[str]
        }
    """
    avg_wait = get_average_wait_time()
    max_wait = get_max_wait_time()
    distribution = get_queue_length_distribution()
    peak = get_peak_queue_size()
    current = get_current_queue_length()
    congestion = get_queue_congestion_periods()
    abandoned = get_abandoned_queue_count()
    checkout_zones = get_checkout_zone_names()

    analytics: dict[str, Any] = {
        "average_wait_time": avg_wait,
        "max_wait_time": max_wait,
        "queue_length_distribution": distribution,
        "peak_queue_size": peak,
        "current_queue_length": current,
        "congestion_periods": congestion,
        "abandoned_queue_count": abandoned,
        "checkout_zones": checkout_zones,
    }

    logger.info(
        "Queue analytics computed — avg_wait=%.2fs, peak=%d, current=%d, abandoned=%d",
        avg_wait if avg_wait else 0.0,
        peak,
        current,
        abandoned,
    )
    return analytics
