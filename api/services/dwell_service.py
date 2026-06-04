"""
Dwell Analytics Service — Dwell Time Analytics

Computes dwell time metrics from the SQLite events table using validated zone polygons.
All values are derived from actual zone_dwell_start and zone_dwell_end events.

Dwell time is calculated from:
- zone_dwell_start: Person enters a zone
- zone_dwell_end: Person exits a zone (contains dwell_seconds in event)

Functions:
    get_average_dwell_per_zone()      → dict[str, float]
    get_max_dwell_per_zone()          → dict[str, float]
    get_min_dwell_per_zone()          → dict[str, float]
    get_dwell_distribution()          → dict[str, list[float]]
    get_overall_average_dwell()       → float | None
    get_dwell_analytics()             → dict  (aggregate convenience wrapper)

Data source:
    events table via api.db.sqlite helpers

Event type mapping:
    zone_dwell_start  → Track enters zone
    zone_dwell_end    → Track exits zone (has dwell_seconds field)
"""

import logging
from typing import Any

from api.db.sqlite import fetchone, fetchall_as_dict

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("dwell_service")


# ---------------------------------------------------------------------------
# Individual Dwell Metric Functions
# ---------------------------------------------------------------------------


def get_average_dwell_per_zone() -> dict[str, float]:
    """
    Compute average dwell time (in seconds) per zone.

    Only considers zone_dwell_end events which contain the dwell_seconds field.
    Returns a dict keyed by zone name with average dwell time.

    Returns:
        {"checkout_zone": 45.3, "entry_zone": 2.1, ...}
    """
    rows = fetchall_as_dict(
        """
        SELECT
            zone,
            AVG(dwell_seconds) AS avg_dwell
        FROM events
        WHERE event_type = ?
          AND dwell_seconds IS NOT NULL
          AND dwell_seconds > 0
        GROUP BY zone
        ORDER BY zone
        """,
        ("zone_dwell_end",),
    )

    result = {row["zone"]: round(row["avg_dwell"], 2) for row in rows}
    logger.debug("Average dwell per zone: %s", result)
    return result


def get_max_dwell_per_zone() -> dict[str, float]:
    """
    Compute maximum dwell time (in seconds) per zone.

    Returns:
        {"checkout_zone": 120.5, "entry_zone": 5.0, ...}
    """
    rows = fetchall_as_dict(
        """
        SELECT
            zone,
            MAX(dwell_seconds) AS max_dwell
        FROM events
        WHERE event_type = ?
          AND dwell_seconds IS NOT NULL
          AND dwell_seconds > 0
        GROUP BY zone
        ORDER BY zone
        """,
        ("zone_dwell_end",),
    )

    result = {row["zone"]: round(row["max_dwell"], 2) for row in rows}
    logger.debug("Max dwell per zone: %s", result)
    return result


def get_min_dwell_per_zone() -> dict[str, float]:
    """
    Compute minimum dwell time (in seconds) per zone.

    Returns:
        {"checkout_zone": 5.2, "entry_zone": 0.5, ...}
    """
    rows = fetchall_as_dict(
        """
        SELECT
            zone,
            MIN(dwell_seconds) AS min_dwell
        FROM events
        WHERE event_type = ?
          AND dwell_seconds IS NOT NULL
          AND dwell_seconds > 0
        GROUP BY zone
        ORDER BY zone
        """,
        ("zone_dwell_end",),
    )

    result = {row["zone"]: round(row["min_dwell"], 2) for row in rows}
    logger.debug("Min dwell per zone: %s", result)
    return result


def get_dwell_distribution() -> dict[str, list[float]]:
    """
    Get raw dwell time distribution (all dwell values) per zone.

    Returns all dwell_seconds values grouped by zone for statistical analysis
    or histogram generation.

    Returns:
        {"checkout_zone": [45.3, 67.1, 23.5, ...], "entry_zone": [2.1, 1.8, ...], ...}
    """
    rows = fetchall_as_dict(
        """
        SELECT
            zone,
            dwell_seconds
        FROM events
        WHERE event_type = ?
          AND dwell_seconds IS NOT NULL
          AND dwell_seconds > 0
        ORDER BY zone, dwell_seconds
        """,
        ("zone_dwell_end",),
    )

    # Group by zone
    distribution: dict[str, list[float]] = {}
    for row in rows:
        zone = row["zone"]
        dwell = round(row["dwell_seconds"], 2)
        if zone not in distribution:
            distribution[zone] = []
        distribution[zone].append(dwell)

    logger.debug("Dwell distribution computed for %d zones", len(distribution))
    return distribution


def get_overall_average_dwell() -> float | None:
    """
    Compute overall average dwell time across all zones.

    Returns:
        Average dwell time in seconds, or None if no dwell data exists.
    """
    row = fetchone(
        """
        SELECT AVG(dwell_seconds) AS avg_dwell
        FROM events
        WHERE event_type = ?
          AND dwell_seconds IS NOT NULL
          AND dwell_seconds > 0
        """,
        ("zone_dwell_end",),
    )

    if row and row["avg_dwell"] is not None:
        avg = round(row["avg_dwell"], 2)
        logger.debug("Overall average dwell: %.2fs", avg)
        return avg

    logger.debug("Overall average dwell: no data")
    return None


def get_zone_dwell_count() -> dict[str, int]:
    """
    Get count of dwell events per zone.

    Returns:
        {"checkout_zone": 15, "entry_zone": 3, ...}
    """
    rows = fetchall_as_dict(
        """
        SELECT
            zone,
            COUNT(*) AS cnt
        FROM events
        WHERE event_type = ?
          AND dwell_seconds IS NOT NULL
          AND dwell_seconds > 0
        GROUP BY zone
        ORDER BY zone
        """,
        ("zone_dwell_end",),
    )

    result = {row["zone"]: row["cnt"] for row in rows}
    logger.debug("Dwell count per zone: %s", result)
    return result


# ---------------------------------------------------------------------------
# Aggregate Convenience Function
# ---------------------------------------------------------------------------


def get_dwell_analytics() -> dict[str, Any]:
    """
    Return comprehensive dwell analytics as a single dict.

    Returns:
        {
            "average_dwell_per_zone": {"zone": float, ...},
            "max_dwell_per_zone": {"zone": float, ...},
            "min_dwell_per_zone": {"zone": float, ...},
            "dwell_distribution": {"zone": [float, ...], ...},
            "overall_average_dwell": float | None,
            "dwell_count_per_zone": {"zone": int, ...}
        }
    """
    average_per_zone = get_average_dwell_per_zone()
    max_per_zone = get_max_dwell_per_zone()
    min_per_zone = get_min_dwell_per_zone()
    distribution = get_dwell_distribution()
    overall_avg = get_overall_average_dwell()
    count_per_zone = get_zone_dwell_count()

    analytics: dict[str, Any] = {
        "average_dwell_per_zone": average_per_zone,
        "max_dwell_per_zone": max_per_zone,
        "min_dwell_per_zone": min_per_zone,
        "dwell_distribution": distribution,
        "overall_average_dwell": overall_avg,
        "dwell_count_per_zone": count_per_zone,
    }

    logger.info(
        "Dwell analytics computed — zones=%d, overall_avg=%.2fs",
        len(average_per_zone),
        overall_avg if overall_avg else 0.0,
    )
    return analytics
