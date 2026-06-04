"""
Funnel Analytics Service -- Task 4.4

Computes a 4-stage customer conversion funnel from the SQLite events table.
Each stage count is derived from actual events -- no hardcoded values.

Stages (in order):
    1. entered_store      -- distinct track_ids with person_entered events
    2. browsed_any_zone   -- of those, tracks that visited any product zone
    3. reached_checkout   -- of those, tracks that appeared in checkout_zone
    4. completed_purchase -- from POS data (placeholder 0 until POS fusion is implemented)

Rules (per TASKS.md Task 4.4):
    - Each stage count must be <= previous stage count
    - No double counting within a session
    - Percentages relative to stage 1
"""

import logging
from typing import Any

from api.db.sqlite import fetchall_as_dict

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("funnel_service")

# ---------------------------------------------------------------------------
# Zone classification helpers
# ---------------------------------------------------------------------------

# Zones that count as "browsing a product area"
# Any zone that is NOT entry_zone, exit_zone, or checkout_zone is a product zone
_NON_PRODUCT_ZONES = {"entry_zone", "exit_zone", "checkout_zone"}


def _is_product_zone(zone: str) -> bool:
    """Return True if the zone qualifies as a product browsing zone."""
    return zone not in _NON_PRODUCT_ZONES


# ---------------------------------------------------------------------------
# Core Funnel Logic
# ---------------------------------------------------------------------------


def get_funnel_stages(store_id: str | None = None) -> list[dict[str, Any]]:
    """
    Compute the 4-stage conversion funnel from events.

    Returns a list of stage dicts:
        [
            {"stage": "entered_store",      "count": int, "percentage": float},
            {"stage": "browsed_any_zone",   "count": int, "percentage": float},
            {"stage": "reached_checkout",   "count": int, "percentage": float},
            {"stage": "completed_purchase", "count": int, "percentage": float},
        ]
    """
    # Stage 1: distinct track_ids that entered the store
    if store_id and store_id != 'shared':
        entered_rows = fetchall_as_dict(
            "SELECT DISTINCT track_id FROM events WHERE event_type = ? AND store_id = ?",
            ("person_entered", store_id),
        )
    else:
        entered_rows = fetchall_as_dict(
            "SELECT DISTINCT track_id FROM events WHERE event_type = ?",
            ("person_entered",),
        )
    entered_tracks = {row["track_id"] for row in entered_rows}
    entered_count = len(entered_tracks)

    # Stage 2: of entered tracks, those that visited any product zone
    # We look for zone_dwell_start or zone_dwell_end events in product zones,
    # OR any event in a product zone for that track
    if entered_tracks:
        placeholders = ",".join("?" for _ in entered_tracks)
        browsed_rows = fetchall_as_dict(
            f"""
            SELECT DISTINCT track_id
            FROM events
            WHERE track_id IN ({placeholders})
              AND zone NOT IN ('entry_zone', 'exit_zone', 'checkout_zone')
              AND event_type IN ('zone_dwell_start', 'zone_dwell_end')
            """,
            tuple(entered_tracks),
        )
        browsed_tracks = {row["track_id"] for row in browsed_rows}
    else:
        browsed_tracks = set()
    browsed_count = len(browsed_tracks)

    # Stage 3: of entered tracks, those that reached checkout_zone
    # We check for any event in checkout_zone (queue_detected, zone_dwell_start, etc.)
    if entered_tracks:
        checkout_rows = fetchall_as_dict(
            f"""
            SELECT DISTINCT track_id
            FROM events
            WHERE track_id IN ({placeholders})
              AND zone = 'checkout_zone'
            """,
            tuple(entered_tracks),
        )
        checkout_tracks = {row["track_id"] for row in checkout_rows}
    else:
        checkout_tracks = set()
    checkout_count = len(checkout_tracks)

    # Stage 4: completed purchase -- from POS fusion
    from api.services.pos_fusion import get_conversion_metrics
    try:
        conversion = get_conversion_metrics(unique_visitors=entered_count, store_id=store_id)
    except TypeError:
        conversion = get_conversion_metrics(unique_visitors=entered_count)
    
    purchase_count = conversion.get("buyers", 0)

    # Enforce monotonic decrease (each stage <= previous)
    browsed_count = min(browsed_count, entered_count)
    checkout_count = min(checkout_count, browsed_count)
    purchase_count = min(purchase_count, checkout_count)

    # Build stages with percentages relative to stage 1
    def _pct(count: int) -> float:
        if entered_count == 0:
            return 0.0
        return round((count / entered_count) * 100, 2)

    stages = [
        {"stage": "entered_store", "count": entered_count, "percentage": _pct(entered_count)},
        {"stage": "browsed_any_zone", "count": browsed_count, "percentage": _pct(browsed_count)},
        {"stage": "reached_checkout", "count": checkout_count, "percentage": _pct(checkout_count)},
        {"stage": "completed_purchase", "count": purchase_count, "percentage": _pct(purchase_count)},
    ]

    logger.info(
        "Funnel computed -- entered=%d, browsed=%d, checkout=%d, purchased=%d",
        entered_count, browsed_count, checkout_count, purchase_count,
    )
    return stages


def get_funnel_data(store_id: str | None = None) -> dict[str, Any]:
    """
    Return the full funnel response matching API_SPEC.md shape.

    Returns:
        {
            "stages": [...],
            "overall_conversion_rate": float
        }
    """
    stages = get_funnel_stages(store_id)
    entered = stages[0]["count"] if stages else 0
    purchased = stages[-1]["count"] if stages else 0

    overall_rate = round((purchased / entered) * 100, 2) if entered > 0 else 0.0

    return {
        "stages": stages,
        "overall_conversion_rate": overall_rate,
    }
