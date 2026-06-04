"""
Redis Event Consumer — Detector Event to SQLite Persistence

Consumes events from Redis queue and persists them to SQLite database.
Matches detector event schema from detector/services/event_generator.py.

Event Schema (from detector):
    {
        "event_id": str (UUID-based),
        "event_type": str (person_entered | person_exited | zone_dwell_start | zone_dwell_end | queue_detected),
        "track_id": int,
        "timestamp": str (ISO-8601),
        "frame_no": int,
        "zone": str,
        "dwell_seconds": float | None,
        "metadata": dict (confidence, bbox, etc.)
    }

Database Schema (from schema.sql):
    events table: event_id, event_type, track_id, timestamp, frame_no, zone, dwell_seconds, metadata

Redis Transport:
    Current: BRPOP from 'store_events_queue' (blocking list)
    Future: Redis Streams 'store:events' (not yet implemented)
"""

import json
import logging
import time
from typing import Any

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logger = logging.getLogger("consumer")


# ---------------------------------------------------------------------------
# Event Validation
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = {"event_id", "event_type", "track_id", "timestamp", "frame_no", "zone"}
VALID_EVENT_TYPES = {"person_entered", "person_exited", "zone_dwell_start", "zone_dwell_end", "queue_detected"}


def validate_event(event_data: dict[str, Any]) -> tuple[bool, str]:
    """
    Validate event data against detector schema.

    Returns:
        (is_valid, error_message)
    """
    # Check required fields
    missing = REQUIRED_FIELDS - set(event_data.keys())
    if missing:
        return False, f"Missing required fields: {missing}"

    # Validate event_type
    event_type = event_data.get("event_type")
    if event_type not in VALID_EVENT_TYPES:
        return False, f"Invalid event_type: {event_type}. Expected one of {VALID_EVENT_TYPES}"

    # Validate types
    if not isinstance(event_data["track_id"], int):
        return False, f"track_id must be int, got {type(event_data['track_id'])}"

    if not isinstance(event_data["frame_no"], int):
        return False, f"frame_no must be int, got {type(event_data['frame_no'])}"

    # Validate optional fields
    if "dwell_seconds" in event_data and event_data["dwell_seconds"] is not None:
        if not isinstance(event_data["dwell_seconds"], (int, float)):
            return False, f"dwell_seconds must be numeric, got {type(event_data['dwell_seconds'])}"

    return True, ""


# ---------------------------------------------------------------------------
# Event Processing
# ---------------------------------------------------------------------------


def process_event(event_data: dict[str, Any]) -> None:
    """
    Process and persist a single event to SQLite.

    Args:
        event_data: Event dict matching detector schema

    Raises:
        Exception: If database insertion fails
    """
    # Import here to avoid circular dependencies
    from api.db.sqlite import execute

    # Validate event
    is_valid, error_msg = validate_event(event_data)
    if not is_valid:
        logger.error("Event validation failed: %s", error_msg)
        logger.debug("Invalid event data: %s", event_data)
        return

    try:
        # Extract metadata as JSON string
        metadata = event_data.get("metadata")
        metadata_json = json.dumps(metadata) if metadata else None

        # Insert event into database
        execute(
            """
            INSERT INTO events (event_id, store_id, event_type, track_id, timestamp, frame_no, zone, dwell_seconds, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_data["event_id"],
                event_data.get("store_id", "store_1"),
                event_data["event_type"],
                event_data["track_id"],
                event_data["timestamp"],
                event_data["frame_no"],
                event_data["zone"],
                event_data.get("dwell_seconds"),
                metadata_json,
            ),
        )

        logger.debug(
            "Event persisted: type=%s, track_id=%d, zone=%s",
            event_data["event_type"],
            event_data["track_id"],
            event_data["zone"],
        )

    except Exception as e:
        logger.error("Error persisting event to database: %s", str(e))
        logger.debug("Failed event data: %s", event_data)
        raise


# ---------------------------------------------------------------------------
# Consumer Loop
# ---------------------------------------------------------------------------


def start_event_consumer() -> None:
    """
    Start the Redis event consumer loop.

    Continuously polls Redis queue for events and persists them to SQLite.
    Blocks on BRPOP with 1-second timeout for graceful shutdown.

    Note: Currently uses BRPOP from 'store_events_queue' (blocking list).
          Future: Migrate to Redis Streams 'store:events' with consumer groups.
    """
    logger.info("Redis consumer worker initialized")

    # Initialize database
    from api.db.sqlite import initialize_db
    initialize_db()

    event_count = 0
    error_count = 0

    while True:
        try:
            # Import Redis client
            from api.redis_client import RedisClient

            client = RedisClient.get_client()
            if not client:
                logger.warning("Redis client not available, retrying in 5 seconds...")
                time.sleep(5)
                continue

            # Pop event from queue (blocks for 1 second)
            res = client.brpop("store_events_queue", timeout=1)

            if res:
                _, payload = res

                # Parse JSON payload
                try:
                    event_data = json.loads(payload)
                except json.JSONDecodeError as e:
                    logger.error("Failed to parse event JSON: %s", e)
                    logger.debug("Invalid JSON payload: %s", payload)
                    error_count += 1
                    continue

                # Process event
                process_event(event_data)
                event_count += 1

                if event_count % 100 == 0:
                    logger.info(
                        "Consumer stats: %d events processed, %d errors",
                        event_count,
                        error_count,
                    )

        except KeyboardInterrupt:
            logger.info("Consumer shutdown requested")
            break

        except Exception as e:
            logger.error("Consumer loop error: %s", str(e))
            error_count += 1
            time.sleep(2)  # Brief pause before retry

    logger.info(
        "Consumer stopped. Final stats: %d events processed, %d errors",
        event_count,
        error_count,
    )


# ---------------------------------------------------------------------------
# Entry Point (for standalone execution)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    start_event_consumer()
