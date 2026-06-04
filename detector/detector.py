import numpy as np
from utils.logger import setup_logger

logger = setup_logger("detector")

class YOLODetector:
    def __init__(self, model_path="models/yolov8n.pt"):
        self.model_path = model_path
        self.is_mock = True
        logger.info(f"Initializing YOLODetector with model: {model_path} (Simulation/Mock Mode Enabled)")

    def detect(self, frame):
        """
        Detects persons in the frame.
        Returns a list of dicts: [{'bbox': [x1, y1, x2, y2], 'confidence': float, 'class_id': 0}]
        """
        # In a real environment:
        # results = self.model(frame)
        # and extract boxes where class_id == 0 (person)
        
        # Simulating detections for demonstration purposes
        detections = []
        # We simulate a dynamic scene with random/scrolling coordinates
        return detections
