"""
YOLOv8n Person Detector -- Task 2.1

Detects people in video frames using YOLOv8n.
Only returns person-class detections (class 0).

Output per frame:
    [
        {"bbox": [x1, y1, x2, y2], "confidence": float},
        ...
    ]
"""

import logging
import os
from typing import Any

import numpy as np

logger = logging.getLogger("detector")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_CONFIDENCE = float(os.environ.get("DETECTION_CONFIDENCE", "0.35"))
PERSON_CLASS_ID = 0  # COCO class 0 = person
MODEL_NAME = os.environ.get("YOLO_MODEL", "models/yolov8n.pt")


class PersonDetector:
    """
    YOLOv8n-based person detector.

    Detects only people (COCO class 0) with configurable confidence.
    """

    def __init__(self, confidence: float = DEFAULT_CONFIDENCE, device: str | None = None):
        """
        Initialize the YOLOv8n model.

        Args:
            confidence: Minimum confidence threshold for detections.
            device: Device to run on ('cpu', 'cuda', '0', etc.).
                    Auto-detected if None.
        """
        self.confidence = confidence
        self.device = device

        # Lazy import to avoid import overhead in tests
        from ultralytics import YOLO

        logger.info("Loading YOLOv8n model: %s (confidence=%.2f)", MODEL_NAME, confidence)
        self.model = YOLO(MODEL_NAME)

        if device:
            self.model.to(device)

        logger.info("YOLOv8n model loaded successfully.")

    def detect(self, frame: np.ndarray) -> list[dict[str, Any]]:
        """
        Run person detection on a single frame.

        Args:
            frame: BGR image as numpy array (H, W, 3).

        Returns:
            List of detections:
                [{"bbox": [x1, y1, x2, y2], "confidence": float}, ...]
        """
        results = self.model(
            frame,
            conf=self.confidence,
            classes=[PERSON_CLASS_ID],
            verbose=False,
        )

        detections: list[dict[str, Any]] = []

        for result in results:
            if result.boxes is None:
                continue

            boxes = result.boxes
            for i in range(len(boxes)):
                xyxy = boxes.xyxy[i].cpu().numpy()
                conf = float(boxes.conf[i].cpu().numpy())

                detections.append({
                    "bbox": [
                        int(xyxy[0]),  # x1
                        int(xyxy[1]),  # y1
                        int(xyxy[2]),  # x2
                        int(xyxy[3]),  # y2
                    ],
                    "confidence": round(conf, 4),
                })

        return detections

    def detect_for_tracking(self, frame: np.ndarray) -> Any:
        """
        Run detection and return raw ultralytics Results for use
        with built-in ByteTrack tracker.

        Returns the raw model output (needed by tracker.py).
        """
        results = self.model.track(
            frame,
            conf=self.confidence,
            classes=[PERSON_CLASS_ID],
            persist=True,
            tracker="bytetrack.yaml",
            verbose=False,
        )
        return results
