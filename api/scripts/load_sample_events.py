"""
Seed Event Loader — Task 3.3.1

Loads sample_events.json into the SQLite events table so that API
routes and the dashboard can be developed before the detector pipeline
is complete.

Usage:
    python api/scripts/load_sample_events.py
"""

import json
import logging
import os
import sys
from typing import Any

# ---------------------------------------------------------------------------
# Ensure project root is on sys.path so api.db.sqlite can be imported
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from api.db.sqlite import execute, fetchone, initialize_db, get_connection

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SAMPLE_EVENTS_PATH = os.environ.get(
    "SAMPLE_EVENTS_PATH",
    os.path.join(PROJECT_ROOT, "data", "sample", "sample_events.json"),
)

# Valid event types from TASKS.md / API_SPEC.md
VALID_EVENT_TYPES = {
    "person_entered",
    "person_exited",
    "zone_dwell_start",
    "zone_dwell_end",
    "queue_detected",
    "anomaly_detected",
    "recommendation_generated",
}

# Required fields in every event
REQUIRED_FIELDS = {"event_id", "event_type", "timestamp", "track_id", "frame_no", "zone"}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("seed_loader")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_event(event: dict[str, Any], index: int) -> list[str]:
    """
    Validate a single event dict against the required schema.

    Returns a list of error messages (empty = valid).
    """
    errors: list[str] = []

    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in event:
            errors.append(f"Event #{index}: missing required field '{field}'")

    # Check event_type is valid
    event_type = event.get("event_type")
    if event_type and event_type not in VALID_EVENT_TYPES:
        errors.append(
            f"Event #{index}: unknown event_type '{event_type}' "
            f"(valid: {sorted(VALID_EVENT_TYPES)})"
        )

    # Basic type checks
    if "track_id" in event and not isinstance(event["track_id"], int):
        errors.append(f"Event #{index}: track_id must be an integer")

    if "frame_no" in event and not isinstance(event["frame_no"], int):
        errors.append(f"Event #{index}: frame_no must be an integer")

    return errors


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------


def extract_dwell_seconds(event: dict[str, Any]) -> float | None:
    """
    Extract dwell_seconds from event or its metadata.

    The sample schema uses metadata.dwell_duration_seconds for
    zone_dwell_end events.
    """
    # Direct field
    if "dwell_seconds" in event and event["dwell_seconds"] is not None:
        return float(event["dwell_seconds"])

    # From metadata
    meta = event.get("metadata", {})
    if isinstance(meta, dict):
        if "dwell_duration_seconds" in meta:
            return float(meta["dwell_duration_seconds"])

    return None


def load_sample_events(filepath: str | None = None) -> tuple[int, int, int]:
    """
    Load sample events from JSON into the SQLite events table.

    Returns (total_loaded, total_skipped, total_errors).
    """
    filepath = filepath or SAMPLE_EVENTS_PATH

    if not os.path.isfile(filepath):
        logger.error("Sample events file not found: %s", filepath)
        raise FileNotFoundError(f"Sample events file not found: {filepath}")

    # Read JSON
    with open(filepath, "r", encoding="utf-8") as f:
        events = json.load(f)

    if not isinstance(events, list):
        logger.error("sample_events.json must contain a JSON array")
        raise ValueError("sample_events.json must contain a JSON array")

    logger.info("Loaded %d event(s) from %s", len(events), filepath)

    total_loaded = 0
    total_skipped = 0
    total_errors = 0

    for i, event in enumerate(events):
        # Validate
        errors = validate_event(event, i)
        if errors:
            for err in errors:
                logger.warning(err)
            total_errors += 1
            continue

        # Check for duplicate
        existing = fetchone(
            "SELECT id FROM events WHERE event_id = ?",
            (event["event_id"],),
        )
        if existing is not None:
            logger.debug("Skipping duplicate event_id=%s", event["event_id"])
            total_skipped += 1
            continue

        # Extract fields
        event_id = event["event_id"]
        event_type = event["event_type"]
        track_id = event["track_id"]
        timestamp = event["timestamp"]
        frame_no = event["frame_no"]
        zone = event["zone"]
        dwell_seconds = extract_dwell_seconds(event)
        metadata_json = json.dumps(event.get("metadata", {}), ensure_ascii=False)

        # Insert
        try:
            execute(
                """
                INSERT INTO events (event_id, event_type, track_id, timestamp, frame_no, zone, dwell_seconds, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (event_id, event_type, track_id, timestamp, frame_no, zone, dwell_seconds, metadata_json),
            )
            total_loaded += 1
        except Exception as exc:
            logger.error("Failed to insert event %s: %s", event_id, exc)
            total_errors += 1

    return total_loaded, total_skipped, total_errors


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the seed event loader."""
    logger.info("=== Seed Event Loader Start ===")

    # Ensure schema exists
    initialize_db()

    loaded, skipped, errors = load_sample_events()

    print(f"\n{'='*60}")
    print(f"  Seed Event Loader Complete")
    print(f"  Inserted: {loaded} events")
    print(f"  Skipped (duplicates): {skipped}")
    print(f"  Errors: {errors}")
    print(f"{'='*60}\n")

    # Verify by counting rows
    row = fetchone("SELECT COUNT(*) as cnt FROM events")
    if row:
        print(f"  Total events in database: {row['cnt']}")

    logger.info("=== Seed Event Loader Complete ===")


if __name__ == "__main__":
    main()
