"""
Redis Event Publisher

Publishes detector-generated events to Redis queue for consumer processing.

Configuration (via environment):
    REDIS_HOST: Redis server hostname (default: localhost)
    REDIS_PORT: Redis server port (default: 6379)
    REDIS_ENABLED: Enable Redis publishing (default: true)

Features:
    - Graceful fallback if Redis unavailable
    - Preserves JSON file output even when Redis enabled
    - Configurable via environment variables
    - Thread-safe singleton pattern
"""

import json
import logging
import os
from typing import Any

logger = logging.getLogger("redis_publisher")


class RedisPublisher:
    """
    Singleton Redis publisher for detector events.
    
    Publishes events to 'store_events_queue' Redis list using LPUSH.
    Consumer uses BRPOP for FIFO ordering.
    """
    
    _instance = None
    _client = None
    _enabled = True
    
    def __init__(self):
        """Initialize Redis publisher (use get_instance() instead)."""
        raise RuntimeError("Use RedisPublisher.get_instance() instead")
    
    @classmethod
    def get_instance(cls) -> "RedisPublisher":
        """Get singleton instance of RedisPublisher."""
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self) -> None:
        """Initialize Redis connection."""
        # Check if Redis is enabled
        self._enabled = os.getenv("REDIS_ENABLED", "true").lower() in ("true", "1", "yes")
        
        if not self._enabled:
            logger.info("Redis publishing disabled via REDIS_ENABLED=false")
            return
        
        # Get configuration
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        
        # Try to connect
        try:
            import redis
            
            self._client = redis.Redis(
                host=redis_host,
                port=redis_port,
                socket_timeout=3,
                socket_connect_timeout=3,
                decode_responses=True,
            )
            
            # Test connection
            self._client.ping()
            logger.info(
                "Redis publisher initialized: %s:%d",
                redis_host,
                redis_port,
            )
            
        except ImportError:
            logger.warning("redis-py not installed, Redis publishing disabled")
            self._enabled = False
            self._client = None
            
        except Exception as e:
            logger.warning(
                "Redis connection failed (%s:%d): %s. Publishing disabled.",
                redis_host,
                redis_port,
                str(e),
            )
            self._enabled = False
            self._client = None
    
    def publish_event(self, event: dict[str, Any]) -> bool:
        """
        Publish a single event to Redis queue.
        
        Args:
            event: Event dict matching detector schema
            
        Returns:
            True if published successfully, False otherwise
        """
        if not self._enabled or not self._client:
            return False
        
        try:
            # Serialize event to JSON
            payload = json.dumps(event)
            
            # Push to Redis list (LPUSH for FIFO with BRPOP)
            self._client.lpush("store_events_queue", payload)
            
            logger.debug(
                "Published event: type=%s, track_id=%d",
                event.get("event_type"),
                event.get("track_id"),
            )
            
            return True
            
        except Exception as e:
            logger.error("Failed to publish event to Redis: %s", str(e))
            return False
    
    def publish_events(self, events: list[dict[str, Any]]) -> tuple[int, int]:
        """
        Publish multiple events to Redis queue.
        
        Args:
            events: List of event dicts
            
        Returns:
            Tuple of (successful_count, failed_count)
        """
        if not self._enabled or not self._client:
            return 0, len(events)
        
        success_count = 0
        fail_count = 0
        
        try:
            # Use pipeline for batch publishing
            pipe = self._client.pipeline()
            
            for event in events:
                try:
                    payload = json.dumps(event)
                    pipe.lpush("store_events_queue", payload)
                    success_count += 1
                except Exception as e:
                    logger.error("Failed to serialize event: %s", str(e))
                    fail_count += 1
            
            # Execute pipeline
            pipe.execute()
            
            logger.debug(
                "Published %d events to Redis (%d failed)",
                success_count,
                fail_count,
            )
            
            return success_count, fail_count
            
        except Exception as e:
            logger.error("Failed to publish events batch to Redis: %s", str(e))
            return 0, len(events)
    
    def is_enabled(self) -> bool:
        """Check if Redis publishing is enabled and connected."""
        return self._enabled and self._client is not None
    
    def get_queue_length(self) -> int:
        """
        Get current length of the event queue.
        
        Returns:
            Queue length, or -1 if Redis unavailable
        """
        if not self._enabled or not self._client:
            return -1
        
        try:
            return self._client.llen("store_events_queue")
        except Exception as e:
            logger.error("Failed to get queue length: %s", str(e))
            return -1
    
    def flush_queue(self) -> bool:
        """
        Clear all events from the queue (for testing).
        
        Returns:
            True if successful, False otherwise
        """
        if not self._enabled or not self._client:
            return False
        
        try:
            self._client.delete("store_events_queue")
            logger.info("Event queue flushed")
            return True
        except Exception as e:
            logger.error("Failed to flush queue: %s", str(e))
            return False


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------


def publish_event(event: dict[str, Any]) -> bool:
    """Publish a single event to Redis (convenience function)."""
    publisher = RedisPublisher.get_instance()
    return publisher.publish_event(event)


def publish_events(events: list[dict[str, Any]]) -> tuple[int, int]:
    """Publish multiple events to Redis (convenience function)."""
    publisher = RedisPublisher.get_instance()
    return publisher.publish_events(events)


def is_redis_enabled() -> bool:
    """Check if Redis publishing is enabled."""
    publisher = RedisPublisher.get_instance()
    return publisher.is_enabled()
