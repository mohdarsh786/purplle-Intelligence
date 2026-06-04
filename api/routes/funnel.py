"""
GET /funnel -- Task 5.3

Returns the customer conversion funnel.
Uses funnel_service.py to compute stages from actual events.

Response shape (per API_SPEC.md):
    {
        "success": true,
        "data": {
            "stages": [...],
            "overall_conversion_rate": float
        }
    }
"""

import logging
from typing import Any

from fastapi import APIRouter

from api.services.funnel_service import get_funnel_data

logger = logging.getLogger("funnel_route")

router = APIRouter()


@router.get("/funnel")
def get_funnel() -> dict[str, Any]:
    """
    Funnel endpoint -- returns 4-stage customer conversion funnel.

    Stages: entered_store -> browsed_any_zone -> reached_checkout -> completed_purchase
    """
    data = get_funnel_data()

    logger.info(
        "Funnel served -- stages: %s",
        ", ".join(f"{s['stage']}={s['count']}" for s in data["stages"]),
    )

    return {"success": True, "data": data}
