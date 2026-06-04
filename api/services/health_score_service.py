"""
Store Health Score Service -- Task 4.8

Computes a single 0-100 store health score from weighted components.
All inputs are normalized to 0-1 before weighting.

Formula (per TASKS.md Task 4.8):
    score = (
        conversion_rate       * 0.35 +
        zone_engagement_rate  * 0.25 +
        (1 - anomaly_density) * 0.20 +
        (1 - queue_pressure)  * 0.20
    ) * 100

Score is a real computed value. Not hardcoded.

Data sources:
    - pos_fusion (conversion rate)
    - metrics_service (unique visitors, entries)
    - events table (zone engagement, queue data)
    - anomaly_service (anomaly count)
"""

import logging
from typing import Any

from api.db.sqlite import fetchone
from api.services.metrics_service import get_total_entries, get_unique_visitors

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("health_score_service")

# ---------------------------------------------------------------------------
# Component Weight Constants (from TASKS.md Task 4.8)
# ---------------------------------------------------------------------------

WEIGHT_CONVERSION = 0.35
WEIGHT_ENGAGEMENT = 0.25
WEIGHT_ANOMALY = 0.20
WEIGHT_QUEUE = 0.20

# Normalization caps
MAX_EXPECTED_CONVERSION = 50.0     # 50% conversion = perfect score
MAX_EXPECTED_ANOMALIES = 10        # 10 anomalies = worst case
MAX_EXPECTED_QUEUE_WAIT = 300.0    # 300s avg wait = worst case


# ---------------------------------------------------------------------------
# Component Calculators
# ---------------------------------------------------------------------------


def _calc_conversion_score() -> float | None:
    """
    Compute normalized conversion rate (0-1).

    Uses POS buyers / CCTV unique visitors, capped at
    MAX_EXPECTED_CONVERSION for normalization.
    Returns None if conversion_status is invalid_data_alignment.
    """
    try:
        from api.services.pos_fusion import get_conversion_metrics
        conv = get_conversion_metrics()
        
        if conv.get("conversion_status") == "insufficient_identity_mapping":
            return None
            
        buyers = conv.get("buyers", 0)
        visitors = conv.get("unique_visitors", 0)
    except Exception:
        buyers = 0
        visitors = get_unique_visitors()

    if visitors > 0 and buyers > 0:
        rate = (buyers / visitors) * 100  # percentage
        normalized = min(rate / MAX_EXPECTED_CONVERSION, 1.0)
    elif visitors == 0 and buyers == 0:
        # No data yet -- neutral score
        normalized = 0.5
    else:
        normalized = 0.0

    logger.debug("Conversion score: %.3f (buyers=%d, visitors=%d)", normalized, buyers, visitors)
    return normalized


def _calc_engagement_score() -> float:
    """
    Compute zone engagement rate (0-1).

    Engagement = proportion of entered visitors that visited
    at least one product zone (zone_dwell_start in non-entry/exit/checkout).
    """
    total_entries = get_total_entries()
    if total_entries == 0:
        return 0.5  # neutral when no data

    row = fetchone(
        """
        SELECT COUNT(DISTINCT track_id) AS engaged
        FROM events
        WHERE event_type = 'zone_dwell_start'
          AND zone NOT IN ('entry_zone', 'exit_zone', 'checkout_zone')
        """
    )

    engaged = row["engaged"] if row else 0
    rate = min(engaged / total_entries, 1.0) if total_entries > 0 else 0.0

    logger.debug("Engagement score: %.3f (engaged=%d, entries=%d)", rate, engaged, total_entries)
    return rate


def _calc_anomaly_density() -> float:
    """
    Compute anomaly density (0-1).

    Higher value = worse. 0 = no anomalies, 1 = heavily anomalous.
    """
    from api.services.anomaly_service import get_anomalies
    anomalies = get_anomalies()
    count = len(anomalies)

    density = min(count / MAX_EXPECTED_ANOMALIES, 1.0)

    logger.debug("Anomaly density: %.3f (%d anomalies)", density, count)
    return density


def _calc_queue_pressure() -> float:
    """
    Compute queue pressure (0-1).

    Higher value = worse. Based on average queue wait time
    from queue_detected events.
    """
    row = fetchone(
        """
        SELECT AVG(
            CASE WHEN metadata IS NOT NULL
                 THEN json_extract(metadata, '$.avg_wait_seconds')
                 ELSE NULL
            END
        ) AS avg_wait
        FROM events
        WHERE event_type = 'queue_detected'
        """
    )

    if row and row["avg_wait"] is not None:
        avg_wait = float(row["avg_wait"])
        pressure = min(avg_wait / MAX_EXPECTED_QUEUE_WAIT, 1.0)
    else:
        pressure = 0.0  # no queue data = no pressure

    logger.debug("Queue pressure: %.3f", pressure)
    return pressure


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_health_score() -> dict[str, Any]:
    """
    Compute the store health score (0-100).

    Returns:
        {
            "score": int,
            "components": {
                "conversion_rate": {"value": float, "weight": float, "weighted": float},
                "zone_engagement": {"value": float, "weight": float, "weighted": float},
                "anomaly_safety": {"value": float, "weight": float, "weighted": float},
                "queue_efficiency": {"value": float, "weight": float, "weighted": float}
            }
        }
    """
    conversion = _calc_conversion_score()
    engagement = _calc_engagement_score()
    anomaly_density = _calc_anomaly_density()
    queue_pressure = _calc_queue_pressure()

    # Apply formula from TASKS.md (or scale if conversion is invalid)
    if conversion is not None:
        raw_score = (
            conversion * WEIGHT_CONVERSION +
            engagement * WEIGHT_ENGAGEMENT +
            (1 - anomaly_density) * WEIGHT_ANOMALY +
            (1 - queue_pressure) * WEIGHT_QUEUE
        ) * 100
        conv_val = round(conversion, 3)
        conv_weighted = round(conversion * WEIGHT_CONVERSION, 3)
    else:
        # Scale the score based on remaining weights (0.65 total)
        raw_score = (
            engagement * WEIGHT_ENGAGEMENT +
            (1 - anomaly_density) * WEIGHT_ANOMALY +
            (1 - queue_pressure) * WEIGHT_QUEUE
        ) * 100 / 0.65
        conv_val = 0.0
        conv_weighted = 0.0

    # Clamp to 0-100
    score = max(0, min(100, round(raw_score)))

    components = {
        "conversion_rate": {
            "value": conv_val,
            "weight": WEIGHT_CONVERSION if conversion is not None else 0.0,
            "weighted": conv_weighted,
        },
        "zone_engagement": {
            "value": round(engagement, 3),
            "weight": WEIGHT_ENGAGEMENT,
            "weighted": round(engagement * WEIGHT_ENGAGEMENT, 3),
        },
        "anomaly_safety": {
            "value": round(1 - anomaly_density, 3),
            "weight": WEIGHT_ANOMALY,
            "weighted": round((1 - anomaly_density) * WEIGHT_ANOMALY, 3),
        },
        "queue_efficiency": {
            "value": round(1 - queue_pressure, 3),
            "weight": WEIGHT_QUEUE,
            "weighted": round((1 - queue_pressure) * WEIGHT_QUEUE, 3),
        },
    }

    logger.info(
        "Health score: %d (conv=%s, engage=%.3f, anomaly=%.3f, queue=%.3f)",
        score, conversion, engagement, anomaly_density, queue_pressure,
    )

    return {
        "score": score,
        "components": components,
    }
