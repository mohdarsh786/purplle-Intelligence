"""
GET /metrics -- Task 5.2 (Extended)

Returns primary business metrics including footfall, conversion,
and store health score. Uses metrics_service, pos_fusion, and
health_score_service.

Response shape (per API_SPEC.md):
    {
        "success": true,
        "data": {
            "footfall": {
                "total_entries": int,
                "total_exits": int,
                "current_store_count": int,
                "unique_visitors": int
            },
            "hourly_footfall": { "00": 0, ..., "23": 0 },
            "conversion": {
                "buyers": int,
                "conversion_rate": float,
                "methodology": str
            },
            "store_health_score": int,
            "warnings": [...]
        }
    }
"""

import logging
from typing import Any

from fastapi import APIRouter

from api.services.metrics_service import get_footfall_metrics
from api.services.pos_fusion import get_conversion_metrics
from api.services.health_score_service import get_health_score

logger = logging.getLogger("metrics_route")

router = APIRouter()

# Minimum visitor threshold before we flag sample-size warning
SAMPLE_SIZE_WARNING_THRESHOLD = 10


@router.get("/metrics")
def get_metrics() -> dict[str, Any]:
    """
    Metrics endpoint -- returns all available business metrics.

    Includes: footfall, conversion, store_health_score.
    Adds sample-size warning when unique_visitors < 10.
    """
    # Footfall
    footfall_data = get_footfall_metrics()
    hourly = footfall_data.pop("hourly_footfall", {})

    footfall = {
        "total_entries": footfall_data["total_entries"],
        "total_exits": footfall_data["total_exits"],
        "current_store_count": footfall_data["current_store_count"],
        "unique_visitors": footfall_data["unique_visitors"],
    }

    # Conversion (from POS fusion)
    conversion = get_conversion_metrics(
        unique_visitors=footfall["unique_visitors"]
    )

    # Store health score
    health = get_health_score()

    # Build response
    data: dict[str, Any] = {
        "footfall": footfall,
        "hourly_footfall": hourly,
        "conversion": {
            "buyers": conversion["buyers"],
            "unique_visitors": conversion.get("unique_visitors", footfall["unique_visitors"]),
            "conversion_rate": conversion["conversion_rate"],
            "conversion_status": conversion.get("conversion_status", "valid"),
            "methodology": conversion["methodology"],
        },
        "store_health_score": health["score"],
    }

    # Warnings
    warnings: list[str] = []
    if footfall["unique_visitors"] < SAMPLE_SIZE_WARNING_THRESHOLD:
        warnings.append(
            f"Low sample size: only {footfall['unique_visitors']} unique visitor(s) detected. "
            f"Metrics may not be statistically representative. "
            f"Minimum recommended: {SAMPLE_SIZE_WARNING_THRESHOLD}."
        )
    if warnings:
        data["warnings"] = warnings

    conv_rate_str = f"{conversion['conversion_rate']:.2f}%" if conversion['conversion_rate'] is not None else "N/A"
    logger.info(
        "Metrics served -- entries=%d, exits=%d, unique=%d, in_store=%d, "
        "buyers=%d, conv_rate=%s, health_score=%d",
        footfall["total_entries"],
        footfall["total_exits"],
        footfall["unique_visitors"],
        footfall["current_store_count"],
        conversion["buyers"],
        conv_rate_str,
        health["score"],
    )

    return {"success": True, "data": data}
