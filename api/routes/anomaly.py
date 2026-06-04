"""
GET /anomaly -- Task 5.5

Returns detected anomalies from rule-based analysis.
Uses anomaly_service.py to detect anomalies from actual events.
Empty list is valid when no thresholds are breached.

Response shape (per API_SPEC.md):
    {
        "success": true,
        "data": {
            "anomalies": [
                {
                    "id": str,
                    "type": str,
                    "severity": str,
                    "zone": str,
                    "description": str,
                    "timestamp": str|null
                }
            ]
        }
    }
"""

import logging
from typing import Any

from fastapi import APIRouter

from api.services.anomaly_service import get_anomaly_data

logger = logging.getLogger("anomaly_route")

router = APIRouter()


@router.get("/anomaly")
def get_anomaly() -> dict[str, Any]:
    """
    Anomaly endpoint -- returns detected operational anomalies.

    Returns an empty list if no thresholds are breached.
    """
    data = get_anomaly_data()

    count = len(data.get("anomalies", []))
    logger.info("Anomaly served -- %d anomalies detected", count)

    return {"success": True, "data": data}
