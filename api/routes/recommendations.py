"""
GET /recommendations -- Task 5.6

Returns actionable business recommendations from rule-based analysis.
Uses recommendation_service.py to generate deterministic recommendations.
Empty list is valid when no thresholds are breached.

Response shape (per API_SPEC.md):
    {
        "success": true,
        "data": {
            "recommendations": [
                {
                    "type": str,
                    "priority": str,
                    "zone": str|null,
                    "business_impact": str,
                    "insight": str,
                    "action": str,
                    "confidence": float
                }
            ]
        }
    }
"""

import logging
from typing import Any

from fastapi import APIRouter

from api.services.recommendation_service import get_recommendation_data

logger = logging.getLogger("recommendations_route")

router = APIRouter()


@router.get("/recommendations")
def get_recommendations() -> dict[str, Any]:
    """
    Recommendations endpoint -- returns actionable business insights.

    All recommendations are deterministic, rule-based. No LLMs.
    """
    data = get_recommendation_data()

    count = len(data.get("recommendations", []))
    logger.info("Recommendations served -- %d recommendations", count)

    return {"success": True, "data": data}
