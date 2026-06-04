import os
import sys
import time
import glob
import cv2
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("main")

from models.detector import PersonDetector
from models.tracker import PersonTracker
from services.event_generator import EventGenerator

ZONES_PATH = os.path.join("data", "zones", "zones.json")
# Use a higher frame skip to process quickly while still generating real events
FRAME_SKIP = int(os.environ.get("FRAME_SKIP", "30"))
CONFIDENCE = float(os.environ.get("DETECTION_CONFIDENCE", "0.35"))

def process_video(video_path: str, store_id: str):
    logger.info(f"Processing video: {video_path} for store: {store_id}")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Cannot open video: {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    detector = PersonDetector(confidence=CONFIDENCE)
    tracker = PersonTracker(max_lost_frames=30)
    
    # Initialize event generator
    event_gen = EventGenerator(
        zones_path=ZONES_PATH,
        video_fps=fps,
        frame_width=width,
        frame_height=height,
        enable_redis=True,
        store_id=store_id
    )

    frame_no = 0
    processed_count = 0
    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_no += 1
        if frame_no % FRAME_SKIP != 0:
            continue

        processed_count += 1
        results = detector.detect_for_tracking(frame)
        tracked_objects = tracker.update(results, frame_no)
        event_gen.process_frame(tracked_objects, frame_no)

        if processed_count % 50 == 0:
            logger.info(f"[{store_id}] {os.path.basename(video_path)}: Frame {frame_no}/{total_frames} - Tracks: {tracker.get_active_count()}")

    cap.release()
    event_gen.finalize()
    
    elapsed = time.time() - start_time
    logger.info(f"Finished {os.path.basename(video_path)} in {elapsed:.1f}s. Generated {len(event_gen.get_all_events())} events.")

def main():
    logger.info("Starting Multi-Store Detector Pipeline...")
    base_dir = os.path.join("data", "stores")
    
    videos_to_process = []
    
    # Discover videos
    for store_id in ["store_1", "store_2"]:
        pattern = os.path.join(base_dir, store_id, "videos", "*.mp4")
        for video_path in glob.glob(pattern):
            videos_to_process.append((video_path, store_id))
            
    if not videos_to_process:
        logger.error("No videos found to process!")
        return
        
    logger.info(f"Found {len(videos_to_process)} videos to process.")
    
    # Wait for Redis and API to be ready before starting
    time.sleep(5)
    
    for video_path, store_id in videos_to_process:
        process_video(video_path, store_id)
        
    logger.info("All videos processed successfully. Exiting detector pipeline.")

    # Keep container alive if needed by docker-compose
    while True:
        time.sleep(60)

if __name__ == "__main__":
    main()
