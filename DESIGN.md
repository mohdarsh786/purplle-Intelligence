# System Design

## System Architecture
Store Intelligence is built on a decoupled publisher/subscriber model. The detector processes raw MP4 CCTV files offline and publishes lightweight tracking events over a Redis queue. The consumer handles DB insertion logic. Finally, the FastAPI backend queries the DB and serves a React frontend.

## Detection Pipeline
- Discover `.mp4` video feeds under `data/stores/*/videos/`.
- Run YOLOv8n object detection (Class 0 / Person) per frame.
- Feed detections into the tracker.

## Tracking Pipeline
Bounding boxes across contiguous frames are cross-referenced using Intersection over Union (IoU) and linear assignment to assign consistent `track_id` values. Re-entry smoothing handles temporary occlusions.

## ReID Strategy
Currently, ReID is not implemented to save on processing overhead and CPU execution time in Docker. The system relies entirely on spatial IoU tracking.

## Store Partitioning
The system employs explicit `store_id` partitioning. 
- The **Detector** injects `store_id` (inferred from file path) into the Redis payload.
- The **Consumer** validates `store_id` as a `NOT NULL` schema requirement.
- The **API** filters all analytical queries natively by `WHERE store_id = ?`.

## Analytics Architecture
The API service dynamically aggregates raw events via SQL group-bys and window functions. All metrics (footfall, queue lengths, top journeys) are calculated dynamically on the fly based on the chosen `store_id`.

## Database Design
SQLite schema revolves around a unified `events` table (partitioned by `store_id`, `event_type`, `track_id`, `timestamp`) and configuration metadata.

## Scalability
Decoupling the computer vision inference (Detector) from the data sink (Consumer) via a Redis queue allows multiple detector nodes to run simultaneously without risking database locking or dropped frames.

## AI-Assisted Decisions
AI assistance proved invaluable in diagnosing silent Docker failures (e.g., SQLite constraint violations dropped events, leading to a silent failure loop). AI helped rewrite the React unified Dashboard component to accurately poll `/api/v1/dashboard?store_id=shared` without introducing cyclical dependency faults.
