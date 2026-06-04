import json
import time
from pydantic import BaseModel
from utils.logger import setup_logger
from utils.config import Config

logger = setup_logger("events")

from typing import Optional, Dict, Any

class CameraEvent(BaseModel):
    event_id: str
    event_type: str
    track_id: int
    timestamp: str
    frame_no: int
    zone: str
    dwell_seconds: Optional[float] = None
    metadata: Dict[str, Any] = {}

class EventPublisher:
    def __init__(self):
        self.redis_client = None
        self.channel = Config.REDIS_CHANNEL
        self.connect()

    def connect(self):
        try:
            import redis
            self.redis_client = redis.Redis(
                host=Config.REDIS_HOST,
                port=Config.REDIS_PORT,
                socket_timeout=3,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Connected successfully to Redis Event Broker.")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {str(e)}. Streaming will operate via local logging only.")
            self.redis_client = None

    def publish(self, event: CameraEvent):
        payload = event.model_dump_json()
        dwell_str = f"{event.dwell_seconds:.1f}" if event.dwell_seconds is not None else "0.0"
        logger.info(f"EVENT GENERATED: {event.event_type} | Customer #{event.track_id} in {event.zone.upper()} (Duration: {dwell_str}s)")
        
        if self.redis_client:
            try:
                # Push event to a list queue (for worker consumption) and also pub/sub for real-time dashboard listeners
                self.redis_client.lpush("store_events_queue", payload)
                self.redis_client.publish(self.channel, payload)
            except Exception as e:
                logger.error(f"Redis publication failed: {str(e)}")
