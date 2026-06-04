# Store Intelligence System

## Project Overview
Physical retail stores lack the real-time analytics capabilities of e-commerce platforms. The Store Intelligence system bridges this gap by transforming raw CCTV video feeds into actionable metrics such as footfall, conversion rates, and heatmaps without relying on cloud APIs or violating privacy.

## Architecture
The system employs a microservices architecture:
1. **Detector:** A PyTorch-based pipeline using YOLOv8n to extract tracks from MP4 video feeds.
2. **Consumer:** Ingests Redis payloads and standardizes them into a central SQLite repository.
3. **API (FastAPI):** Serves aggregated metrics, health scores, and dynamically routes anomalies/recommendations.
4. **Dashboard (React):** A dynamic UI providing visual tracking and store-partitioned intelligence.

## Setup Instructions
1. Clone the repository.
2. Ensure you have Python 3.11 installed.
3. Use the unified `docker-compose up -d` to launch all services.

## Docker Instructions
```bash
docker-compose build
docker-compose up -d
```
All dependencies (Redis, Python runtimes, Node.js builds) are containerized. 

## API Endpoints
- `GET /api/v1/dashboard`: Unified aggregation (accepts `?store_id=store_1`)
- `GET /api/v1/feed/status`: Discovers available cameras per store.
- `GET /api/v1/feed/video`: Serves MP4 streams for specific cameras.

## Dashboard Features
The dashboard features an aesthetic dark-mode layout powered by React and CSS Grid. It provides real-time visualizations for Live Cameras, Anomaly Feeds, Funnels, and Queue status, completely partitioned by store.

## Detector Pipeline
The detector ingests mp4 video frames, identifies people using YOLOv8n, tracks them across contiguous frames with an IoU tracker, and publishes semantic events to a Redis queue.

## Store Analytics
Analytics are completely partitioned per physical store location using the `store_id` identifier. Query endpoints calculate footfall, queue times, and journey paths on-the-fly.

## Event Generation
Tracks crossing predefined zone polygons emit semantic lifecycle events (`person_entered`, `zone_dwell_start`, `person_exited`).

## Future Improvements
- **Staff Exclusion:** Exclude store employees from footfall metrics by detecting uniform colors or staff lanyards.
- **DeepSORT Integration:** For deep occlusions where IoU tracking loses track identity.
