import time
from db.sqlite import get_db_connection
from redis_client import RedisClient

class HealthService:
    @staticmethod
    def check_health():
        health = {
            "status": "healthy",
            "database": "disconnected",
            "redis": "disconnected",
            "uptime_seconds": 0
        }
        
        # Test Database
        try:
            conn = get_db_connection()
            conn.cursor().execute("SELECT 1")
            conn.close()
            health["database"] = "connected"
        except Exception:
            health["status"] = "unhealthy"
            
        # Test Redis
        try:
            client = RedisClient.get_client()
            if client and client.ping():
                health["redis"] = "connected"
        except Exception:
            pass
            
        return health
