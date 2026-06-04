import json
import os
from utils.logger import setup_logger

logger = setup_logger("zones")

def is_point_in_polygon(point, polygon):
    """
    Ray-casting algorithm to determine if a point is inside a polygon.
    point: (x, y)
    polygon: List of points [(x1, y1), (x2, y2), ...]
    """
    x, y = point
    n = len(polygon)
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

class ZoneManager:
    def __init__(self, config_path):
        self.config_path = config_path
        self.zones = {}
        self.load_zones()

    def load_zones(self):
        if not os.path.exists(self.config_path):
            # Create a default set of zones if config doesn't exist
            default_zones = [
                {
                    "id": "entrance",
                    "name": "Entrance Lobby",
                    "polygon": [[0, 0], [400, 0], [400, 300], [0, 300]]
                },
                {
                    "id": "apparel",
                    "name": "Apparel Section",
                    "polygon": [[400, 0], [1280, 0], [1280, 350], [400, 350]]
                },
                {
                    "id": "electronics",
                    "name": "Electronics Hub",
                    "polygon": [[0, 300], [600, 300], [600, 720], [0, 720]]
                },
                {
                    "id": "checkout",
                    "name": "Checkout Counters",
                    "polygon": [[600, 350], [1280, 350], [1280, 720], [600, 720]]
                }
            ]
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_zones, f, indent=4)
            logger.info(f"Created default zones list at {self.config_path}")

        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
                for item in data:
                    self.zones[item["id"]] = {
                        "name": item["name"],
                        "polygon": item["polygon"]
                    }
            logger.info(f"Loaded {len(self.zones)} operational retail zones successfully.")
        except Exception as e:
            logger.error(f"Failed to load zones configuration: {str(e)}")

    def check_point(self, point):
        """Returns the zone_id representing where the point is located, or None"""
        for zone_id, zone_data in self.zones.items():
            if is_point_in_polygon(point, zone_data["polygon"]):
                return zone_id
        return None
