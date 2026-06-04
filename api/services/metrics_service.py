"""
Footfall Metrics Service — Task 4.1

Computes footfall metrics from the SQLite events table.
All values are derived from actual events — no hardcoded values.

Functions:
    get_total_entries()      → int
    get_total_exits()        → int
    get_unique_visitors()    → int
    get_currently_in_store() → int
    get_hourly_footfall()    → dict[str, int]
    get_footfall_metrics()   → dict  (aggregate convenience wrapper)

Data source:
    events table via api.db.sqlite helpers

Event type mapping:
    person_entered  → entry count
    person_exited   → exit count
    unique visitors → COUNT(DISTINCT track_id) on person_entered events
    currently_in_store → entries − exits (floored at 0)
"""

import logging
from typing import Any

from api.db.sqlite import fetchone, fetchall_as_dict

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("metrics_service")


# ---------------------------------------------------------------------------
# Individual Metric Functions
# ---------------------------------------------------------------------------


def get_total_entries(store_id: str | None = None) -> int:
    """
    Count the total number of person_entered events.

    Returns:
        Total entry count from the events table.
    """
    query = "SELECT COUNT(*) AS cnt FROM events WHERE event_type = ?"
    params = ["person_entered"]
    if store_id and store_id != "shared":
        query += " AND store_id = ?"
        params.append(store_id)
        
    row = fetchone(query, tuple(params))
    count = row["cnt"] if row else 0
    logger.debug("Total entries: %d", count)
    return count


def get_total_exits(store_id: str | None = None) -> int:
    """
    Count the total number of person_exited events.

    Returns:
        Total exit count from the events table.
    """
    query = "SELECT COUNT(*) AS cnt FROM events WHERE event_type = ?"
    params = ["person_exited"]
    if store_id and store_id != "shared":
        query += " AND store_id = ?"
        params.append(store_id)
        
    row = fetchone(query, tuple(params))
    count = row["cnt"] if row else 0
    logger.debug("Total exits: %d", count)
    return count


def get_unique_visitors(store_id: str | None = None) -> int:
    """
    Count unique visitors by distinct track_id on person_entered events.

    This gives the deduplicated visitor count. When the re-entry
    matching logic is active in the detector, tracks that belong to the
    same physical visitor share a track_id, so COUNT(DISTINCT track_id)
    already reflects deduplication.

    Returns:
        Number of unique visitor track IDs.
    """
    query = "SELECT COUNT(DISTINCT track_id) AS cnt FROM events WHERE event_type = ?"
    params = ["person_entered"]
    if store_id and store_id != "shared":
        query += " AND store_id = ?"
        params.append(store_id)
        
    row = fetchone(query, tuple(params))
    count = row["cnt"] if row else 0
    logger.debug("Unique visitors: %d", count)
    return count


def get_currently_in_store(store_id: str | None = None) -> int:
    """
    Estimate the number of people currently inside the store.

    Calculation: total entries − total exits, floored at 0.

    Returns:
        Non-negative integer representing current occupancy.
    """
    entries = get_total_entries(store_id)
    exits = get_total_exits(store_id)
    current = max(0, entries - exits)
    logger.debug("Currently in store: %d (entries=%d, exits=%d)", current, entries, exits)
    return current


def get_hourly_footfall(store_id: str | None = None) -> dict[str, int]:
    """
    Compute entry counts grouped by hour of day.

    Returns a dict keyed by 2-digit hour string ("00" .. "23")
    with the count of person_entered events in that hour.
    Hours with zero entries are included for completeness.

    Returns:
        e.g. {"08": 0, "09": 5, "10": 12, ...}
    """
    # Extract hour from ISO-8601 timestamp: "2026-04-10T18:30:01Z" → "18"
    query = """
        SELECT
            substr(timestamp, 12, 2) AS hour,
            COUNT(*)                 AS cnt
        FROM events
        WHERE event_type = ?
    """
    params = ["person_entered"]
    if store_id and store_id != "shared":
        query += " AND store_id = ?"
        params.append(store_id)
    
    query += " GROUP BY hour ORDER BY hour"
    
    rows = fetchall_as_dict(query, tuple(params))

    # Build a full 24-hour dict, defaulting missing hours to 0
    hourly: dict[str, int] = {f"{h:02d}": 0 for h in range(24)}
    for row in rows:
        hour_key = row["hour"]
        if hour_key in hourly:
            hourly[hour_key] = row["cnt"]

    logger.debug("Hourly footfall: %s", hourly)
    return hourly


# ---------------------------------------------------------------------------
# Aggregate Convenience Function
# ---------------------------------------------------------------------------


def get_footfall_metrics(store_id: str | None = None) -> dict[str, Any]:
    """
    Return all footfall metrics as a single dict matching the
    API_SPEC.md `footfall` response shape.

    Returns:
        {
            "total_entries": int,
            "total_exits": int,
            "unique_visitors": int,
            "current_store_count": int,
            "hourly_footfall": dict[str, int]
        }
    """
    metrics: dict[str, Any] = {
        "total_entries": get_total_entries(store_id),
        "total_exits": get_total_exits(store_id),
        "unique_visitors": get_unique_visitors(store_id),
        "current_store_count": get_currently_in_store(store_id),
        "hourly_footfall": get_hourly_footfall(store_id),
    }

    logger.info(
        "Footfall metrics computed — entries=%d, exits=%d, unique=%d, in_store=%d",
        metrics["total_entries"],
        metrics["total_exits"],
        metrics["unique_visitors"],
        metrics["current_store_count"],
    )
    return metrics
