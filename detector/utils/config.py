import os

class Config:
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_CHANNEL = os.getenv("REDIS_CHANNEL", "store_events")
    ZONES_CONFIG_PATH = os.getenv("ZONES_CONFIG_PATH", "../data/zones/zones.json")
    CAMERA_SOURCE = os.getenv("CAMERA_SOURCE", "mock")
    FRAME_WIDTH = int(os.getenv("FRAME_WIDTH", 1280))
    FRAME_HEIGHT = int(os.getenv("FRAME_HEIGHT", 720))
    DWELL_ALERT_THRESHOLD = int(os.getenv("DWELL_ALERT_THRESHOLD", 30))  # seconds
