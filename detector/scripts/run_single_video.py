"""
Single Video Pipeline Runner -- Task 2.7 (Validation)

Runs the full detection pipeline on a single video file:
    Video → YOLO Detector → ByteTrack Tracker → Event Generator → events.json

Usage:
    python detector/scripts/run_single_video.py [VIDEO_PATH]

    If VIDEO_PATH is not provided, uses the first video in data/videos/.

Output:
    data/output/events.json
"""

import json
import logging
import os
import sys
import time
from pathlib import Path

# Ensure project root is importable
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import cv2
import numpy as np

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("run_single_video")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_VIDEO_DIR = os.path.join("data", "videos")
OUTPUT_DIR = os.path.join("data", "output")
ZONES_PATH = os.path.join("data", "zones", "zones.json")
FRAME_SKIP = int(os.environ.get("FRAME_SKIP", "3"))  # Process 1 of every N frames
CONFIDENCE = float(os.environ.get("DETECTION_CONFIDENCE", "0.35"))
LOG_INTERVAL = 100  # Log progress every N processed frames


def find_video(path: str | None = None) -> str:
    """Find a video file to process."""
    if path and os.path.isfile(path):
        return path

    # Search data/videos for .mp4 files
    if os.path.isdir(DEFAULT_VIDEO_DIR):
        for f in sorted(os.listdir(DEFAULT_VIDEO_DIR)):
            if f.lower().endswith(".mp4"):
                return os.path.join(DEFAULT_VIDEO_DIR, f)

    raise FileNotFoundError("No video file found. Provide path or place .mp4 in data/videos/")


def run_pipeline(video_path: str) -> str:
    """
    Run the full detection pipeline on a single video.

    Returns path to the output events.json file.
    """
    from detector.models.detector import PersonDetector
    from detector.models.tracker import PersonTracker
    from detector.services.event_generator import EventGenerator

    # Open video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps if fps > 0 else 0

    logger.info("=" * 60)
    logger.info("Video: %s", os.path.basename(video_path))
    logger.info("Resolution: %dx%d, FPS: %.2f", width, height, fps)
    logger.info("Total frames: %d, Duration: %.1fs", total_frames, duration)
    logger.info("Frame skip: %d (processing 1 of every %d)", FRAME_SKIP, FRAME_SKIP)
    logger.info("Confidence threshold: %.2f", CONFIDENCE)
    logger.info("=" * 60)

    # Initialize pipeline components
    detector = PersonDetector(confidence=CONFIDENCE)
    tracker = PersonTracker(max_lost_frames=30)
    event_gen = EventGenerator(
        zones_path=ZONES_PATH,
        video_fps=fps,
        video_start_time="2026-04-10T16:45:00Z",  # Same date as POS data
        frame_width=width,
        frame_height=height,
    )

    # Process frames
    frame_no = 0
    processed_count = 0
    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_no += 1

        # Frame skip
        if frame_no % FRAME_SKIP != 0:
            continue

        processed_count += 1

        # Detection + Tracking (combined via ultralytics)
        results = detector.detect_for_tracking(frame)

        # Extract tracked objects
        tracked_objects = tracker.update(results, frame_no)

        # Generate events
        events = event_gen.process_frame(tracked_objects, frame_no)

        # Progress logging
        if processed_count % LOG_INTERVAL == 0:
            elapsed = time.time() - start_time
            fps_actual = processed_count / elapsed if elapsed > 0 else 0
            progress = (frame_no / total_frames) * 100 if total_frames > 0 else 0
            logger.info(
                "Progress: frame %d/%d (%.1f%%) | %d events | %.1f fps | %d tracks active",
                frame_no, total_frames, progress,
                len(event_gen.get_all_events()),
                fps_actual,
                tracker.get_active_count(),
            )

    cap.release()

    # Finalize (exit events for remaining tracks)
    event_gen.finalize()

    elapsed = time.time() - start_time
    all_events = event_gen.get_all_events()
    redis_stats = event_gen.get_redis_stats()

    logger.info("=" * 60)
    logger.info("Pipeline complete!")
    logger.info("Processed %d frames in %.1fs (%.1f fps)", processed_count, elapsed, processed_count / elapsed if elapsed > 0 else 0)
    logger.info("Total events generated: %d", len(all_events))
    
    # Redis publishing stats
    if redis_stats["total"] > 0:
        logger.info(
            "Redis publishing: %d published, %d failed (%.1f%% success)",
            redis_stats["published"],
            redis_stats["failed"],
            (redis_stats["published"] / redis_stats["total"] * 100) if redis_stats["total"] > 0 else 0,
        )
    else:
        logger.info("Redis publishing: disabled or not configured")

    # Event type breakdown
    type_counts: dict[str, int] = {}
    for evt in all_events:
        etype = evt["event_type"]
        type_counts[etype] = type_counts.get(etype, 0) + 1

    for etype, count in sorted(type_counts.items()):
        logger.info("  %s: %d", etype, count)

    # Unique tracks
    unique_tracks = set(evt["track_id"] for evt in all_events)
    logger.info("Unique track IDs: %d", len(unique_tracks))
    logger.info("=" * 60)

    # Save output
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "events.json")
    with open(output_path, "w") as f:
        json.dump(all_events, f, indent=2)
    logger.info("Events saved to: %s", output_path)

    return output_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    video_path = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        video = find_video(video_path)
        output = run_pipeline(video)
        print(f"\n✓ Pipeline complete. Events saved to: {output}")
    except FileNotFoundError as e:
        logger.error("Video not found: %s", e)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logger.error("Pipeline failed: %s", e, exc_info=True)
        sys.exit(1)
