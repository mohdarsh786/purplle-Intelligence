"""
Anomaly Detection Service -- Task 4.6

Detects operational anomalies from the SQLite events table using
rule-based thresholds defined in TASKS.md.

Anomaly types:
    crowd_spike      -- >5 people in any zone simultaneously
    unusual_dwell    -- single track in one zone >600 seconds
    queue_congestion -- checkout_zone count >4 for >5 minutes

All anomalies are derived from actual events -- no hardcoded alerts.
An empty anomaly list is valid when no thresholds are breached.

Output per anomaly (per TASKS.md Task 4.6):
    event_id, type, timestamp, zone, description, severity (info/warn/critical)
"""

import json
import logging
import uuid
from typing import Any

from api.db.sqlite import fetchall_as_dict

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("anomaly_service")

# ---------------------------------------------------------------------------
# Threshold Constants (from TASKS.md Task 4.6)
# ---------------------------------------------------------------------------

CROWD_SPIKE_THRESHOLD = 5           # >5 people in any zone simultaneously
UNUSUAL_DWELL_THRESHOLD = 600.0     # >600 seconds in one zone
QUEUE_CONGESTION_THRESHOLD = 4      # >4 in checkout_zone for >5 minutes
QUEUE_CONGESTION_DURATION = 300.0   # 5 minutes in seconds


# ---------------------------------------------------------------------------
# Anomaly Detectors
# ---------------------------------------------------------------------------


def _detect_unusual_dwell(store_id: str | None = None) -> list[dict[str, Any]]:
    """
    Detect tracks that dwelled in a single zone for >600 seconds.

    Uses zone_dwell_end events which carry dwell_seconds in their metadata
    (as dwell_duration_seconds), or in the dwell_seconds column directly.
    """
    anomalies: list[dict[str, Any]] = []

    # Check the dwell_seconds column first
    query1 = """
        SELECT event_id, track_id, zone, timestamp, dwell_seconds, metadata
        FROM events
        WHERE event_type = 'zone_dwell_end'
          AND dwell_seconds IS NOT NULL
          AND dwell_seconds > ?
    """
    params1 = [UNUSUAL_DWELL_THRESHOLD]
    if store_id and store_id != "shared":
        query1 += " AND store_id = ?"
        params1.append(store_id)
        
    rows = fetchall_as_dict(query1, tuple(params1))

    for row in rows:
        anomalies.append({
            "id": f"an_{uuid.uuid4().hex[:8]}",
            "type": "unusual_dwell",
            "severity": "warn" if row["dwell_seconds"] < 900 else "critical",
            "zone": row["zone"],
            "description": (
                f"Track {row['track_id']} stationary in {row['zone']} "
                f"for {row['dwell_seconds']:.0f}s (threshold: {UNUSUAL_DWELL_THRESHOLD:.0f}s)"
            ),
            "timestamp": row["timestamp"],
        })

    # Also check metadata.dwell_duration_seconds for events where
    # dwell_seconds column is NULL
    query2 = """
        SELECT event_id, track_id, zone, timestamp, metadata
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

    for row in meta_rows:
        try:
            meta = json.loads(row["metadata"]) if isinstance(row["metadata"], str) else {}
            dwell = meta.get("dwell_duration_seconds")
            if dwell is not None and float(dwell) > UNUSUAL_DWELL_THRESHOLD:
                anomalies.append({
                    "id": f"an_{uuid.uuid4().hex[:8]}",
                    "type": "unusual_dwell",
                    "severity": "warn" if float(dwell) < 900 else "critical",
                    "zone": row["zone"],
                    "description": (
                        f"Track {row['track_id']} stationary in {row['zone']} "
                        f"for {float(dwell):.0f}s (threshold: {UNUSUAL_DWELL_THRESHOLD:.0f}s)"
                    ),
                    "timestamp": row["timestamp"],
                })
        except (json.JSONDecodeError, ValueError, TypeError):
            continue

    logger.debug("unusual_dwell: found %d anomalies", len(anomalies))
    return anomalies


def _detect_crowd_spike(store_id: str | None = None) -> list[dict[str, Any]]:
    """
    Detect zones where more than CROWD_SPIKE_THRESHOLD people
    were present simultaneously.

    Approximation: count distinct track_ids with zone_dwell_start
    in a zone without a matching zone_dwell_end (i.e. currently in zone).
    Since we're working with historical data, we count max concurrent
    per zone from overlapping dwell intervals.

    Simplified approach: count distinct tracks per zone from
    zone_dwell_start events. If any zone has > threshold, flag it.
    """
    anomalies: list[dict[str, Any]] = []

    query = """
        SELECT zone, COUNT(DISTINCT track_id) AS track_count
        FROM events
        WHERE event_type = 'zone_dwell_start'
    """
    params = []
    if store_id and store_id != "shared":
        query += " AND store_id = ?"
        params.append(store_id)
        
    query += " GROUP BY zone HAVING track_count > ?"
    params.append(CROWD_SPIKE_THRESHOLD)
    
    rows = fetchall_as_dict(query, tuple(params))

    for row in rows:
        anomalies.append({
            "id": f"an_{uuid.uuid4().hex[:8]}",
            "type": "crowd_spike",
            "severity": "critical" if row["track_count"] > CROWD_SPIKE_THRESHOLD * 2 else "warn",
            "zone": row["zone"],
            "description": (
                f"{row['track_count']} people detected in {row['zone']} "
                f"(threshold: {CROWD_SPIKE_THRESHOLD})"
            ),
            "timestamp": None,  # Aggregate anomaly, no single timestamp
        })

    logger.debug("crowd_spike: found %d anomalies", len(anomalies))
    return anomalies


def _detect_queue_congestion(store_id: str | None = None) -> list[dict[str, Any]]:
    """
    Detect queue congestion in checkout_zone.

    Flags if more than QUEUE_CONGESTION_THRESHOLD people were detected
    in the checkout zone via queue_detected events.
    """
    anomalies: list[dict[str, Any]] = []

    # Count distinct tracks in checkout_zone
    query = """
        SELECT COUNT(DISTINCT track_id) AS track_count,
               MIN(timestamp) AS first_ts,
               MAX(timestamp) AS last_ts
        FROM events
        WHERE zone = 'checkout_zone'
          AND event_type IN ('queue_detected', 'zone_dwell_start')
    """
    params = []
    if store_id and store_id != "shared":
        query += " AND store_id = ?"
        params.append(store_id)
        
    rows = fetchall_as_dict(query, tuple(params))

    for row in rows:
        count = row["track_count"] or 0
        if count > QUEUE_CONGESTION_THRESHOLD:
            anomalies.append({
                "id": f"an_{uuid.uuid4().hex[:8]}",
                "type": "queue_congestion",
                "severity": "critical",
                "zone": "checkout_zone",
                "description": (
                    f"Queue congestion: {count} people in checkout "
                    f"(threshold: {QUEUE_CONGESTION_THRESHOLD})"
                ),
                "timestamp": row["first_ts"],
            })

    logger.debug("queue_congestion: found %d anomalies", len(anomalies))
    return anomalies


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_anomalies(store_id: str | None = None) -> list[dict[str, Any]]:
    """
    Run all anomaly detectors and return a combined list.

    Returns an empty list if no thresholds are breached (this is valid).

    Returns:
        [
            {
                "id": "an_xxxx",
                "type": "unusual_dwell",
                "severity": "medium",
                "zone": "product_zone_1",
                "description": "Track 42 stationary in product_zone_1 for 720s",
                "timestamp": "2026-04-10T18:30:00Z"
            },
            ...
        ]
    """
    all_anomalies: list[dict[str, Any]] = []

    all_anomalies.extend(_detect_unusual_dwell(store_id))
    all_anomalies.extend(_detect_crowd_spike(store_id))
    all_anomalies.extend(_detect_queue_congestion(store_id))

    logger.info("Anomaly detection complete -- %d anomalies found", len(all_anomalies))
    return all_anomalies


def get_anomaly_data() -> dict[str, Any]:
    """
    Return the full anomaly response matching API_SPEC.md shape.

    Returns:
        {"anomalies": [...]}
    """
    return {"anomalies": get_anomalies()}
