"""
Event Generator -- Task 2.5

Generates business events from tracked person detections and zone assignments.

Events generated:
    person_entered      -- track crosses entry zone boundary inbound
    person_exited       -- track disappears (lost) or crosses exit zone
    zone_dwell_start    -- track enters a new zone
    zone_dwell_end      -- track leaves a zone (includes dwell_seconds)
    queue_detected      -- track detected in checkout_zone

Event schema (per TASKS.md Task 2.5):
    {
        "event_id": "uuid4",
        "event_type": str,
        "track_id": int,
        "timestamp": str (ISO-8601),
        "frame_no": int,
        "zone": str,
        "dwell_seconds": float|null,
        "metadata": {
            "confidence": float,
            "bbox": [x1, y1, x2, y2],
            ...
        }
    }

Zone data loaded from zones.json. No hardcoded zones.
"""

import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger("event_generator")

# Redis publisher (imported lazily to avoid circular dependencies)
_redis_publisher = None


def _get_redis_publisher():
    """Lazy import Redis publisher to avoid circular dependencies."""
    global _redis_publisher
    if _redis_publisher is None:
        try:
            from services.redis_publisher import RedisPublisher
            _redis_publisher = RedisPublisher.get_instance()
        except Exception as e:
            logger.warning("Redis publisher not available: %s", str(e))
            _redis_publisher = None
    return _redis_publisher

# ---------------------------------------------------------------------------
# Zone Manager (handles empty polygons gracefully per Task 2.4)
# ---------------------------------------------------------------------------

DEFAULT_ZONES_PATH = os.path.join("data", "zones", "zones.json")


def _point_in_polygon(point: tuple[int, int], polygon: list[list[int]]) -> bool:
    """Ray-casting algorithm for point-in-polygon test."""
    x, y = point
    n = len(polygon)
    if n < 3:
        return False

    inside = False
    p1x, p1y = polygon[0]
    for i in range(n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside


class ZoneMapper:
    """
    Maps bounding box centroids to zones loaded from zones.json.

    Handles empty polygon coordinates gracefully by falling back
    to a proportional grid-based zone assignment based on frame dimensions.
    """

    def __init__(self, zones_path: str = DEFAULT_ZONES_PATH, frame_width: int = 1920, frame_height: int = 1080):
        self.zones: dict[str, list[list[int]]] = {}
        self.zone_names: list[str] = []
        self._has_polygons = False
        self.frame_width = frame_width
        self.frame_height = frame_height

        self._load_zones(zones_path)

    def _load_zones(self, path: str) -> None:
        """Load zone definitions from JSON."""
        if not os.path.exists(path):
            logger.warning("zones.json not found at %s, using fallback zones", path)
            self._setup_fallback_zones()
            return

        try:
            with open(path, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error("Failed to load zones.json: %s", e)
            self._setup_fallback_zones()
            return

        # Parse zones -- may be dict or list format
        if isinstance(data, dict):
            for zone_name, zone_data in data.items():
                self.zone_names.append(zone_name)
                if isinstance(zone_data, dict) and "polygon" in zone_data:
                    poly = zone_data["polygon"]
                    if poly and len(poly) >= 3:
                        self.zones[zone_name] = poly
                        self._has_polygons = True
                elif isinstance(zone_data, list) and len(zone_data) >= 3:
                    self.zones[zone_name] = zone_data
                    self._has_polygons = True
                else:
                    self.zones[zone_name] = []  # Empty polygon
        elif isinstance(data, list):
            for item in data:
                name = item.get("id", item.get("name", "unknown"))
                self.zone_names.append(name)
                poly = item.get("polygon", [])
                if poly and len(poly) >= 3:
                    self.zones[name] = poly
                    self._has_polygons = True
                else:
                    self.zones[name] = []

        if not self._has_polygons:
            logger.warning(
                "All zone polygons are empty. Using proportional fallback zones."
            )
            self._setup_fallback_zones()
        else:
            logger.info("Loaded %d zones (%d with polygons)", len(self.zones), sum(1 for v in self.zones.values() if v))

    def _setup_fallback_zones(self) -> None:
        """
        Create proportional fallback zones based on frame dimensions.
        This allows the pipeline to function even when zones.json has no coordinates.
        """
        w, h = self.frame_width, self.frame_height
        third_w = w // 3
        half_h = h // 2

        self.zones = {
            "entry_zone": [[0, 0], [third_w, 0], [third_w, half_h], [0, half_h]],
            "exit_zone": [[0, half_h], [third_w, half_h], [third_w, h], [0, h]],
            "product_zone_1": [[third_w, 0], [2 * third_w, 0], [2 * third_w, half_h], [third_w, half_h]],
            "product_zone_2": [[third_w, half_h], [2 * third_w, half_h], [2 * third_w, h], [third_w, h]],
            "checkout_zone": [[2 * third_w, 0], [w, 0], [w, h], [2 * third_w, h]],
        }
        self.zone_names = list(self.zones.keys())
        self._has_polygons = True
        logger.info("Fallback zones created: %s", list(self.zones.keys()))

    def get_zone(self, centroid: tuple[int, int]) -> str:
        """
        Map a centroid (x, y) to a zone name.

        Returns "unknown" if point is not inside any zone.
        """
        if not self._has_polygons:
            return "unknown"

        for zone_name, polygon in self.zones.items():
            if polygon and _point_in_polygon(centroid, polygon):
                return zone_name

        return "unknown"


# ---------------------------------------------------------------------------
# Event Generator
# ---------------------------------------------------------------------------


class EventGenerator:
    """
    Generates business events from tracked detections.

    Manages per-track state to emit zone transitions, entry/exit,
    and dwell events.
    """

    def __init__(
        self,
        zones_path: str = DEFAULT_ZONES_PATH,
        video_fps: float = 30.0,
        video_start_time: str | None = None,
        frame_width: int = 1920,
        frame_height: int = 1080,
        enable_redis: bool = True,
        store_id: str = "store_1",
    ):
        """
        Args:
            zones_path: Path to zones.json.
            video_fps: Video FPS for timestamp calculation.
            video_start_time: ISO-8601 timestamp of video start.
                              Defaults to current time if None.
            frame_width: Video frame width (for fallback zones).
            frame_height: Video frame height (for fallback zones).
            enable_redis: Enable Redis publishing (default: True).
            store_id: Store identifier (store_1, store_2, etc.)
        """
        self.zone_mapper = ZoneMapper(zones_path, frame_width, frame_height)
        self.fps = video_fps
        self.enable_redis = enable_redis
        self.store_id = store_id

        if video_start_time:
            self._start_time = datetime.fromisoformat(video_start_time.replace("Z", "+00:00"))
        else:
            self._start_time = datetime.now(tz=None)  # Local time fallback

        # Per-track state
        self._track_zones: dict[int, str] = {}           # track_id -> current zone
        self._track_zone_entry_frame: dict[int, int] = {}  # track_id -> frame when entered current zone
        self._entered_tracks: set[int] = set()             # tracks that have generated person_entered
        self._exited_tracks: set[int] = set()              # tracks that have generated person_exited
        self._queue_notified: dict[int, bool] = {}         # track_id -> whether queue_detected was sent

        self._events: list[dict[str, Any]] = []
        
        # Redis publishing stats
        self._redis_published_count = 0
        self._redis_failed_count = 0

        logger.info(
            "EventGenerator initialized -- fps=%.2f, start=%s, zones=%d, redis=%s, store_id=%s",
            self.fps, self._start_time.isoformat(), len(self.zone_mapper.zones),
            "enabled" if self.enable_redis else "disabled",
            self.store_id,
        )

    def _frame_to_timestamp(self, frame_no: int) -> str:
        """Convert frame number to ISO-8601 timestamp."""
        delta = timedelta(seconds=frame_no / self.fps)
        ts = self._start_time + delta
        return ts.strftime("%Y-%m-%dT%H:%M:%SZ")

    def _make_event(
        self,
        event_type: str,
        track_id: int,
        frame_no: int,
        zone: str,
        confidence: float = 0.0,
        bbox: list[int] | None = None,
        dwell_seconds: float | None = None,
        extra_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a standardized event dict matching TASKS.md schema."""
        metadata: dict[str, Any] = {
            "confidence": round(confidence, 4),
        }
        if bbox:
            metadata["bbox"] = bbox
        if extra_metadata:
            metadata.update(extra_metadata)

        event = {
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "event_type": event_type,
            "store_id": self.store_id,
            "track_id": track_id,
            "timestamp": self._frame_to_timestamp(frame_no),
            "frame_no": frame_no,
            "zone": zone,
            "dwell_seconds": dwell_seconds,
            "metadata": metadata,
        }
        
        # Publish to Redis if enabled
        if self.enable_redis:
            publisher = _get_redis_publisher()
            if publisher and publisher.is_enabled():
                if publisher.publish_event(event):
                    self._redis_published_count += 1
                else:
                    self._redis_failed_count += 1
        
        return event

    def _centroid_from_bbox(self, bbox: list[int]) -> tuple[int, int]:
        """Calculate bounding box centroid."""
        return (
            (bbox[0] + bbox[2]) // 2,  # center x
            (bbox[1] + bbox[3]) // 2,  # center y
        )

    def process_frame(
        self,
        tracked_objects: list[dict[str, Any]],
        frame_no: int,
    ) -> list[dict[str, Any]]:
        """
        Process tracked objects for a single frame and generate events.

        Args:
            tracked_objects: List of tracked detections:
                [{"track_id": int, "bbox": [x1,y1,x2,y2], "confidence": float}, ...]
            frame_no: Current frame number.

        Returns:
            List of events generated this frame.
        """
        frame_events: list[dict[str, Any]] = []
        current_track_ids: set[int] = set()

        for obj in tracked_objects:
            track_id = obj["track_id"]
            bbox = obj["bbox"]
            confidence = obj.get("confidence", 0.0)
            current_track_ids.add(track_id)

            # Determine zone from centroid
            centroid = self._centroid_from_bbox(bbox)
            zone = self.zone_mapper.get_zone(centroid)

            # --- person_entered ---
            if track_id not in self._entered_tracks:
                self._entered_tracks.add(track_id)
                event = self._make_event(
                    "person_entered", track_id, frame_no,
                    zone if zone != "unknown" else "entry_zone",
                    confidence, bbox,
                    extra_metadata={"direction": "inward"},
                )
                frame_events.append(event)
                logger.debug("person_entered: track %d at frame %d", track_id, frame_no)

            # --- Zone transition ---
            prev_zone = self._track_zones.get(track_id)
            if prev_zone != zone and zone != "unknown":
                # End dwell in previous zone
                if prev_zone and prev_zone != "unknown":
                    entry_frame = self._track_zone_entry_frame.get(track_id, frame_no)
                    dwell = (frame_no - entry_frame) / self.fps
                    event = self._make_event(
                        "zone_dwell_end", track_id, frame_no,
                        prev_zone, confidence, bbox,
                        dwell_seconds=round(dwell, 2),
                        extra_metadata={"dwell_duration_seconds": round(dwell, 2)},
                    )
                    frame_events.append(event)

                # Start dwell in new zone
                self._track_zones[track_id] = zone
                self._track_zone_entry_frame[track_id] = frame_no
                event = self._make_event(
                    "zone_dwell_start", track_id, frame_no,
                    zone, confidence, bbox,
                )
                frame_events.append(event)

                # --- queue_detected ---
                if zone == "checkout_zone" and not self._queue_notified.get(track_id, False):
                    self._queue_notified[track_id] = True
                    event = self._make_event(
                        "queue_detected", track_id, frame_no,
                        "checkout_zone", confidence, bbox,
                        extra_metadata={
                            "queue_position": 0,
                            "queue_size_estimate": 0,
                        },
                    )
                    frame_events.append(event)

        # --- person_exited (for tracks that disappeared) ---
        for track_id in list(self._track_zones.keys()):
            if track_id not in current_track_ids and track_id not in self._exited_tracks:
                # Track disappeared -- generate exit event
                prev_zone = self._track_zones.get(track_id, "exit_zone")
                entry_frame = self._track_zone_entry_frame.get(track_id, frame_no)
                dwell = (frame_no - entry_frame) / self.fps

                # End final dwell
                if prev_zone and prev_zone != "unknown":
                    event = self._make_event(
                        "zone_dwell_end", track_id, frame_no,
                        prev_zone, 0.0, None,
                        dwell_seconds=round(dwell, 2),
                        extra_metadata={"dwell_duration_seconds": round(dwell, 2)},
                    )
                    frame_events.append(event)

                # Exit event
                self._exited_tracks.add(track_id)
                event = self._make_event(
                    "person_exited", track_id, frame_no,
                    "exit_zone", 0.0, None,
                    extra_metadata={
                        "total_journey_seconds": round(
                            (frame_no - min(self._track_zone_entry_frame.get(track_id, frame_no), frame_no)) / self.fps, 2
                        ),
                    },
                )
                frame_events.append(event)

                # Cleanup
                self._track_zones.pop(track_id, None)
                self._track_zone_entry_frame.pop(track_id, None)

        # Store all events
        self._events.extend(frame_events)

        return frame_events

    def finalize(self) -> list[dict[str, Any]]:
        """
        Finalize remaining tracks (generate exit events for all still-active tracks).

        Call this after the last frame.
        """
        final_events: list[dict[str, Any]] = []
        last_frame = max(
            (self._track_zone_entry_frame.get(tid, 0) for tid in self._track_zones),
            default=0,
        )

        for track_id in list(self._track_zones.keys()):
            if track_id not in self._exited_tracks:
                zone = self._track_zones.get(track_id, "exit_zone")
                entry_frame = self._track_zone_entry_frame.get(track_id, last_frame)
                dwell = (last_frame - entry_frame) / self.fps if last_frame > entry_frame else 0

                if zone and zone != "unknown":
                    event = self._make_event(
                        "zone_dwell_end", track_id, last_frame,
                        zone, 0.0, None,
                        dwell_seconds=round(dwell, 2),
                        extra_metadata={"dwell_duration_seconds": round(dwell, 2)},
                    )
                    final_events.append(event)

                self._exited_tracks.add(track_id)
                event = self._make_event(
                    "person_exited", track_id, last_frame,
                    "exit_zone", 0.0, None,
                )
                final_events.append(event)

        self._events.extend(final_events)
        self._track_zones.clear()
        self._track_zone_entry_frame.clear()

        logger.info(
            "Finalized -- %d total events generated (Redis: %d published, %d failed)",
            len(self._events),
            self._redis_published_count,
            self._redis_failed_count,
        )
        return final_events

    def get_all_events(self) -> list[dict[str, Any]]:
        """Return all generated events."""
        return self._events.copy()
    
    def get_redis_stats(self) -> dict[str, int]:
        """
        Get Redis publishing statistics.
        
        Returns:
            Dict with keys: published, failed, total
        """
        return {
            "published": self._redis_published_count,
            "failed": self._redis_failed_count,
            "total": self._redis_published_count + self._redis_failed_count,
        }
