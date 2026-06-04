"""
Store Intelligence API — FastAPI Application Bootstrap

Entry point for the API service. Initializes the database on startup
and registers all available route modules.

Usage:
    uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

    OR from project root:
    python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
"""

import logging
import os
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.db.sqlite import initialize_db
from api.routes import health, metrics, funnel, journey, anomaly, recommendations, feed, cameras, dashboard

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("api")

# ---------------------------------------------------------------------------
# Application State
# ---------------------------------------------------------------------------
# Startup timestamp — used by /health to compute uptime
APP_START_TIME: float = 0.0

# Store ID from environment (default per TASKS.md Task 5.1)
STORE_ID: str = os.environ.get("STORE_ID", "ST1008")


# ---------------------------------------------------------------------------
# Lifespan (replaces deprecated @app.on_event)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Startup and shutdown lifecycle for the FastAPI application.

    Startup:
        - Initialize SQLite database (auto-creates schema)
        - Record startup timestamp
        - Log readiness

    Shutdown:
        - Log graceful shutdown
    """
    global APP_START_TIME

    logger.info("=== Store Intelligence API Starting ===")

    # Initialize database
    logger.info("Initializing SQLite database...")
    initialize_db()
    logger.info("Database initialized successfully.")

    # Record start time
    APP_START_TIME = time.time()

    logger.info("Store ID: %s", STORE_ID)
    logger.info("=== API Ready — Accepting Requests ===")

    yield  # Application runs here

    logger.info("=== Store Intelligence API Shutting Down ===")


# ---------------------------------------------------------------------------
# FastAPI Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Store Intelligence API",
    description="Backend API for converting CCTV footage into actionable retail intelligence.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow dashboard and dev tools to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Route Registration
# ---------------------------------------------------------------------------

# Base path: /api/v1 (per API_SPEC.md)
API_PREFIX = "/api/v1"

app.include_router(health.router, prefix=API_PREFIX, tags=["Health"])
app.include_router(metrics.router, prefix=API_PREFIX, tags=["Metrics"])
app.include_router(funnel.router, prefix=API_PREFIX, tags=["Funnel"])
app.include_router(journey.router, prefix=API_PREFIX, tags=["Journey"])
app.include_router(anomaly.router, prefix=API_PREFIX, tags=["Anomaly"])
app.include_router(recommendations.router, prefix=API_PREFIX, tags=["Recommendations"])
app.include_router(feed.router, prefix=API_PREFIX, tags=["Feed"])
app.include_router(cameras.router, prefix=API_PREFIX, tags=["Cameras"])
app.include_router(dashboard.router, prefix=API_PREFIX, tags=["Dashboard"])


# ---------------------------------------------------------------------------
# Convenience: run directly with `python api/main.py`
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("API_PORT", "8000"))
    uvicorn.run("api.main:app", host="0.0.0.0", port=port, reload=True)
