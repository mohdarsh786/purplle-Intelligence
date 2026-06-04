# Engineering Choices

## Model Selection
Object detection was required to locate and track individuals in the store. YOLO models balance inference speed and accuracy best.

## YOLO Choice
We chose YOLOv8n over heavy transformer models like DETR because retail CCTV tracking requires exceptionally fast inference on minimal hardware. YOLOv8n operates beautifully on CPU-only Docker instances while providing more than enough accuracy for standard retail settings.

## Tracker Choice
A lightweight bounding-box IoU (Intersection over Union) tracker with linear assignment was implemented. This allows ID persistence without dragging in extremely heavyweight DeepSORT or ReID dependencies that crash in constrained submission environments.

## Redis Choice
Redis provides the necessary buffering layer to decouple the high-throughput detector pipeline from the slower database ingestion logic. It prevents event drops during traffic spikes.

## SQLite Choice
SQLite is a zero-configuration, serverless DB perfectly suited for embedded analytics and hackathon/submission packaging. It easily handles concurrent reads, negating the need for a bulky Postgres service while still allowing robust SQL aggregation.

## FastAPI Choice
FastAPI is async-native and provides out-of-the-box OpenAPI documentation. It allows our microservices to execute non-blocking database queries quickly.

## Frontend Choice
React (Vite) with CSS Grid allows dynamic store rendering and interactive multi-camera mosaics, which is essential for multi-store validation proof.

## Tradeoffs
- We use IoU tracking rather than Re-identification (ReID). While ReID prevents ID swaps during deep occlusions, it drastically impacts performance. IoU tracking is the perfect balance for standard top-down CCTV footage.

## Rejected Alternatives
- **Rejected:** Using PyTorch CUDA builds inside Docker. This bloated images by 2.5GB and failed to launch on machines lacking NVIDIA hardware. 
