"""
GET /journey -- Task 5.4

Returns the most common customer journey paths.
Uses journey_service.py to compute paths from actual events.

Response shape (per API_SPEC.md):
    {
        "success": true,
        "data": {
            "top_paths": [
                {"path": ["zone1", "zone2"], "count": int}
            ],
            "average_journey_duration_seconds": float|null
        }
    }
"""

import logging
from typing import Any

from fastapi import APIRouter

from api.services.journey_service import get_journey_data

logger = logging.getLogger("journey_route")

router = APIRouter()


@router.get("/journey")
def get_journey() -> dict[str, Any]:
    """
    Journey endpoint -- returns top customer paths ranked by frequency.
    """
    data = get_journey_data()

    path_count = len(data.get("top_paths", []))
    avg_dur = data.get("average_journey_duration_seconds")
    logger.info(
        "Journey served -- %d paths, avg_duration=%.1fs",
        path_count,
        avg_dur if avg_dur else 0,
    )

    return {"success": True, "data": data}
