import redis
from utils.config import Config
from utils.logger import setup_logger

logger = setup_logger("redis")

class RedisClient:
    _instance = None
    
    @classmethod
    def get_client(cls):
        if cls._instance is None:
            try:
                cls._instance = redis.Redis(
                    host=Config.REDIS_HOST,
                    port=Config.REDIS_PORT,
                    socket_timeout=3,
                    decode_responses=True
                )
                cls._instance.ping()
                logger.info("RedisClient initialized and pinged successfully.")
            except Exception as e:
                logger.error(f"RedisClient initialization failed: {str(e)}")
                cls._instance = None
        return cls._instance
