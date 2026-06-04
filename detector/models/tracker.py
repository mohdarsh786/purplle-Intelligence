"""
ByteTrack Person Tracker -- Task 2.2

Uses ultralytics built-in ByteTrack via model.track(persist=True).
Maintains stable track IDs across frames with lifecycle management.

Output per frame:
    [
        {"track_id": int, "bbox": [x1, y1, x2, y2], "confidence": float},
        ...
    ]
"""

import logging
import time
from typing import Any

import numpy as np

logger = logging.getLogger("tracker")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

MAX_LOST_FRAMES = 30  # Remove tracks not seen for > 30 frames


class TrackState:
    """Tracks the lifecycle of a single person track."""

    __slots__ = (
        "track_id", "first_seen_frame", "last_seen_frame",
        "first_bbox", "last_bbox", "zone_history",
        "is_active", "confidence",
    )

    def __init__(self, track_id: int, frame_no: int, bbox: list[int], confidence: float):
        self.track_id = track_id
        self.first_seen_frame = frame_no
        self.last_seen_frame = frame_no
        self.first_bbox = bbox
        self.last_bbox = bbox
        self.zone_history: list[str] = []
        self.is_active = True
        self.confidence = confidence


class PersonTracker:
    """
    ByteTrack-based person tracker with lifecycle management.

    Uses ultralytics built-in tracking with persistent IDs.
    Maintains an active track state dict and removes stale tracks.
    """

    def __init__(self, max_lost_frames: int = MAX_LOST_FRAMES):
        """
        Args:
            max_lost_frames: Remove tracks not seen for this many frames.
        """
        self.max_lost_frames = max_lost_frames
        self.tracks: dict[int, TrackState] = {}
        self._frame_count = 0

        logger.info("PersonTracker initialized (max_lost=%d)", max_lost_frames)

    def update(self, results: Any, frame_no: int) -> list[dict[str, Any]]:
        """
        Process tracking results from detector.detect_for_tracking().

        Args:
            results: Raw ultralytics Results from model.track().
            frame_no: Current frame number.

        Returns:
            List of active tracked objects:
                [{"track_id": int, "bbox": [x1,y1,x2,y2], "confidence": float}, ...]
        """
        self._frame_count = frame_no
        current_tracks: list[dict[str, Any]] = []
        seen_ids: set[int] = set()

        for result in results:
            if result.boxes is None or result.boxes.id is None:
                continue

            boxes = result.boxes
            for i in range(len(boxes)):
                track_id = int(boxes.id[i].cpu().numpy())
                xyxy = boxes.xyxy[i].cpu().numpy()
                conf = float(boxes.conf[i].cpu().numpy())

                bbox = [
                    int(xyxy[0]),
                    int(xyxy[1]),
                    int(xyxy[2]),
                    int(xyxy[3]),
                ]

                seen_ids.add(track_id)

                # Update or create track state
                if track_id in self.tracks:
                    ts = self.tracks[track_id]
                    ts.last_seen_frame = frame_no
                    ts.last_bbox = bbox
                    ts.confidence = conf
                    ts.is_active = True
                else:
                    self.tracks[track_id] = TrackState(
                        track_id=track_id,
                        frame_no=frame_no,
                        bbox=bbox,
                        confidence=conf,
                    )
                    logger.debug("New track: %d at frame %d", track_id, frame_no)

                current_tracks.append({
                    "track_id": track_id,
                    "bbox": bbox,
                    "confidence": round(conf, 4),
                })

        # Cleanup stale tracks
        lost_ids = self._cleanup_stale_tracks(frame_no, seen_ids)

        return current_tracks

    def _cleanup_stale_tracks(self, frame_no: int, seen_ids: set[int]) -> list[int]:
        """
        Remove tracks not seen for > max_lost_frames.

        Returns list of track_ids that were removed.
        """
        lost: list[int] = []
        for tid, ts in list(self.tracks.items()):
            if tid not in seen_ids:
                gap = frame_no - ts.last_seen_frame
                if gap > self.max_lost_frames:
                    ts.is_active = False
                    lost.append(tid)
                    logger.debug(
                        "Track %d lost at frame %d (last seen: %d, gap: %d)",
                        tid, frame_no, ts.last_seen_frame, gap,
                    )

        # Remove from active dict
        for tid in lost:
            del self.tracks[tid]

        return lost

    def get_lost_tracks(self, frame_no: int) -> list[TrackState]:
        """
        Get tracks that are about to be removed (gap > max_lost_frames).
        Useful for generating person_exited events.
        """
        lost: list[TrackState] = []
        for tid, ts in self.tracks.items():
            gap = frame_no - ts.last_seen_frame
            if gap > self.max_lost_frames and ts.is_active:
                lost.append(ts)
        return lost

    def get_active_count(self) -> int:
        """Return count of currently active tracks."""
        return len(self.tracks)

    def get_all_track_ids(self) -> list[int]:
        """Return all known active track IDs."""
        return list(self.tracks.keys())
