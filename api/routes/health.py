"""
GET /health — Task 5.1

Returns service health status with live database metrics.
All values are queried from the actual database — no hardcoded counts.

Response shape (per TASKS.md Task 5.1):
    {
        "success": true,
        "data": {
            "status": "ok",
            "store_id": "ST1008",
            "detector_status": "not_started",
            "events_processed": <int>,
            "db_connected": true,
            "last_event_timestamp": <str|null>,
            "uptime_seconds": <int>
        }
    }
"""

import logging
import time
from typing import Any

from fastapi import APIRouter

from api.db.sqlite import fetchone

logger = logging.getLogger("health")

router = APIRouter()


@router.get("/health")
def get_health() -> dict[str, Any]:
    """
    Health check endpoint.

    Queries the SQLite events table for actual counts.
    Returns structured JSON following the API_SPEC.md success envelope.
    """
    # Import here to avoid circular import at module load time
    from api.main import APP_START_TIME, STORE_ID

    # Database connectivity check
    db_connected = True
    events_processed = 0
    last_event_timestamp: str | None = None

    try:
        row = fetchone("SELECT COUNT(*) AS cnt FROM events")
        events_processed = row["cnt"] if row else 0

        ts_row = fetchone(
            "SELECT timestamp FROM events ORDER BY created_at DESC LIMIT 1"
        )
        if ts_row:
            last_event_timestamp = ts_row["timestamp"]
    except Exception as exc:
        logger.error("Database health check failed: %s", exc)
        db_connected = False

    # Uptime calculation
    uptime_seconds = int(time.time() - APP_START_TIME) if APP_START_TIME > 0 else 0

    # Detector status — currently always "not_started" until detector is integrated
    detector_status = "not_started"

    data: dict[str, Any] = {
        "status": "ok" if db_connected else "degraded",
        "store_id": STORE_ID,
        "detector_status": detector_status,
        "events_processed": events_processed,
        "db_connected": db_connected,
        "last_event_timestamp": last_event_timestamp,
        "uptime_seconds": uptime_seconds,
    }

    logger.info(
        "Health check — status=%s, events=%d, db=%s, uptime=%ds",
        data["status"],
        events_processed,
        db_connected,
        uptime_seconds,
    )

    return {"success": True, "data": data}
