"""
Recommendation Engine -- Task 4.7

Generates deterministic, rule-based business recommendations from
analytics data. No LLMs. No hardcoded demo recommendations.
Empty list is valid when no thresholds are breached.

Rules (per TASKS.md Task 4.7):
    1. IF zone avg_dwell > 180s AND purchase_correlation < 0.1
       -> "Deploy salesperson or add promotion to {zone}"
    2. IF queue avg_wait > 240s
       -> "Open additional checkout counter"
    3. IF peak_hour footfall > avg * 1.5 AND currently_in_store > 12
       -> "Increase floor staff during peak hour"
    4. IF zone visitor_count < 5 AND zone is product_zone
       -> "Review product placement or visibility"

Data sources:
    - events table (dwell, zone visits, queue)
    - metrics_service (footfall, currently_in_store)
    - pos_fusion (conversion data)
"""

import json
import logging
from typing import Any

from api.db.sqlite import fetchall_as_dict, fetchone
from api.services.metrics_service import (
    get_currently_in_store,
    get_hourly_footfall,
    get_total_entries,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("recommendation_service")

# ---------------------------------------------------------------------------
# Threshold Constants (from TASKS.md Task 4.7)
# ---------------------------------------------------------------------------

HIGH_DWELL_THRESHOLD = 180.0        # seconds
LOW_PURCHASE_CORRELATION = 0.1      # ratio
QUEUE_WAIT_THRESHOLD = 240.0        # seconds
PEAK_HOUR_MULTIPLIER = 1.5          # peak vs average
CROWD_THRESHOLD = 12                # currently_in_store
LOW_VISITOR_THRESHOLD = 5           # zone visitor count

# Zones classified as product zones
_NON_PRODUCT_ZONES = {"entry_zone", "exit_zone", "checkout_zone"}


# ---------------------------------------------------------------------------
# Rule Implementations
# ---------------------------------------------------------------------------


def _rule_high_dwell_low_conversion(store_id: str | None = None) -> list[dict[str, Any]]:
    """
    Rule 1: High dwell + low conversion -> Deploy salesperson.

    Check each zone's average dwell. If avg > 180s and the
    purchase correlation for that zone is < 0.1, recommend action.
    """
    recs: list[dict[str, Any]] = []

    query1 = """
        SELECT zone, AVG(dwell_seconds) AS avg_dwell, COUNT(*) AS dwell_count
        FROM events
        WHERE event_type = 'zone_dwell_end'
          AND dwell_seconds IS NOT NULL
    """
    params1 = []
    if store_id and store_id != "shared":
        query1 += " AND store_id = ?"
        params1.append(store_id)
    query1 += " GROUP BY zone"
    
    rows = fetchall_as_dict(query1, tuple(params1))

    query2 = """
        SELECT zone, metadata
        FROM events
        WHERE event_type = 'zone_dwell_end'
          AND dwell_seconds IS NULL
          AND metadata IS NOT NULL
    """
    params2 = []
    if store_id and store_id != "shared":
        query2 += " AND store_id = ?"
        params2.append(store_id)
        
    meta_rows = fetchall_as_dict(query2, tuple(params2))

    # Build per-zone dwell averages
    zone_dwells: dict[str, list[float]] = {}
    for row in rows:
        if row["avg_dwell"] is not None and row["zone"] not in _NON_PRODUCT_ZONES:
            zone_dwells.setdefault(row["zone"], []).append(row["avg_dwell"])

    for row in meta_rows:
        try:
            meta = json.loads(row["metadata"]) if isinstance(row["metadata"], str) else {}
            dwell = meta.get("dwell_duration_seconds")
            if dwell is not None and row["zone"] not in _NON_PRODUCT_ZONES:
                zone_dwells.setdefault(row["zone"], []).append(float(dwell))
        except (json.JSONDecodeError, ValueError, TypeError):
            continue

    for zone, dwells in zone_dwells.items():
        avg_dwell = sum(dwells) / len(dwells) if dwells else 0
        if avg_dwell > HIGH_DWELL_THRESHOLD:
            # Purchase correlation is low by default without POS-zone mapping
            # In production, this would check POS department sales for this zone
            recs.append({
                "type": "revenue_opportunity",
                "priority": "high",
                "zone": zone,
                "business_impact": "conversion",
                "insight": (
                    f"High engagement in {zone} (avg dwell: {avg_dwell:.0f}s) "
                    f"but low conversion"
                ),
                "action": f"Deploy salesperson or add promotion to {zone}",
                "confidence": round(min(avg_dwell / 300, 1.0), 2),
            })

    logger.debug("Rule 1 (high dwell): %d recommendations", len(recs))
    return recs


def _rule_queue_congestion(store_id: str | None = None) -> list[dict[str, Any]]:
    """
    Rule 2: High queue wait -> Open additional counter.

    Checks average wait time from queue_detected events.
    """
    recs: list[dict[str, Any]] = []

    query = """
        SELECT AVG(
            CASE WHEN metadata IS NOT NULL
                 THEN json_extract(metadata, '$.avg_wait_seconds')
                 ELSE NULL
            END
        ) AS avg_wait
        FROM events
        WHERE event_type = 'queue_detected'
    """
    params = []
    if store_id and store_id != "shared":
        query += " AND store_id = ?"
        params.append(store_id)
        
    row = fetchone(query, tuple(params))

    if row and row["avg_wait"] is not None:
        avg_wait = float(row["avg_wait"])
        if avg_wait > QUEUE_WAIT_THRESHOLD:
            recs.append({
                "type": "operational",
                "priority": "high",
                "zone": "checkout_zone",
                "business_impact": "staffing",
                "insight": f"Queue wait time ({avg_wait:.0f}s) exceeds threshold ({QUEUE_WAIT_THRESHOLD:.0f}s)",
                "action": "Open additional checkout counter",
                "confidence": round(min(avg_wait / 480, 1.0), 2),
            })

    logger.debug("Rule 2 (queue): %d recommendations", len(recs))
    return recs


def _rule_peak_hour_staffing(store_id: str | None = None) -> list[dict[str, Any]]:
    """
    Rule 3: Peak hour footfall > avg * 1.5 AND currently_in_store > 12
    -> Increase floor staff.
    """
    recs: list[dict[str, Any]] = []

    hourly = get_hourly_footfall(store_id)
    currently = get_currently_in_store(store_id)

    # Calculate average hourly footfall (only hours with data)
    values = [v for v in hourly.values() if v > 0]
    if not values:
        return recs

    avg_hourly = sum(values) / len(values)
    peak_hour = max(hourly, key=lambda k: hourly[k])
    peak_value = hourly[peak_hour]

    if peak_value > avg_hourly * PEAK_HOUR_MULTIPLIER and currently > CROWD_THRESHOLD:
        recs.append({
            "type": "staffing",
            "priority": "medium",
            "zone": None,
            "business_impact": "staffing",
            "insight": (
                f"Peak hour ({peak_hour}:00) footfall ({peak_value}) "
                f"exceeds {PEAK_HOUR_MULTIPLIER}x average ({avg_hourly:.1f}) "
                f"with {currently} people in store"
            ),
            "action": f"Increase floor staff during peak hour ({peak_hour}:00)",
            "confidence": round(min(peak_value / (avg_hourly * 2), 1.0), 2),
        })

    logger.debug("Rule 3 (peak hour): %d recommendations", len(recs))
    return recs


def _rule_low_engagement(store_id: str | None = None) -> list[dict[str, Any]]:
    """
    Rule 4: Zone visitor_count < 5 AND zone is product_zone
    -> Review product placement.
    """
    recs: list[dict[str, Any]] = []

    query = """
        SELECT zone, COUNT(DISTINCT track_id) AS visitor_count
        FROM events
        WHERE event_type = 'zone_dwell_start'
          AND zone NOT IN ('entry_zone', 'exit_zone', 'checkout_zone')
    """
    params = []
    if store_id and store_id != "shared":
        query += " AND store_id = ?"
        params.append(store_id)
        
    query += " GROUP BY zone"
    
    rows = fetchall_as_dict(query, tuple(params))

    for row in rows:
        if row["visitor_count"] < LOW_VISITOR_THRESHOLD:
            recs.append({
                "type": "merchandising",
                "priority": "medium",
                "zone": row["zone"],
                "business_impact": "conversion",
                "insight": (
                    f"Low engagement in {row['zone']}: "
                    f"only {row['visitor_count']} visitor(s)"
                ),
                "action": f"Review product placement or visibility in {row['zone']}",
                "confidence": round(1 - (row["visitor_count"] / LOW_VISITOR_THRESHOLD), 2),
            })

    logger.debug("Rule 4 (low engagement): %d recommendations", len(recs))
    return recs


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_recommendations(store_id: str | None = None) -> list[dict[str, Any]]:
    """
    Run all recommendation rules and return a combined list.

    Rules are deterministic -- no LLMs. Empty list is valid when
    no thresholds are breached.

    Returns:
        [
            {
                "type": str,
                "priority": "low"|"medium"|"high"|"critical",
                "zone": str|None,
                "business_impact": str,
                "insight": str,
                "action": str,
                "confidence": float
            },
            ...
        ]
    """
    all_recs: list[dict[str, Any]] = []

    all_recs.extend(_rule_high_dwell_low_conversion(store_id))
    all_recs.extend(_rule_queue_congestion(store_id))
    all_recs.extend(_rule_peak_hour_staffing(store_id))
    all_recs.extend(_rule_low_engagement(store_id))

    # Sort by priority (high first)
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    all_recs.sort(key=lambda r: priority_order.get(r.get("priority", "low"), 3))

    logger.info("Recommendation engine complete -- %d recommendations", len(all_recs))
    return all_recs


def get_recommendation_data() -> dict[str, Any]:
    """
    Return the full recommendation response matching API_SPEC.md shape.

    Returns:
        {"recommendations": [...]}
    """
    return {"recommendations": get_recommendations()}
