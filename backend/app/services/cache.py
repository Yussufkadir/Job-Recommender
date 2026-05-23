import os
import logging

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

redis_client = None
try:
    import redis
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    logger.info("Redis client initialized")
except ImportError:
    logger.info("Redis not installed, caching disabled")
except Exception as e:
    logger.warning("Redis connection failed: %s", e)

def user_app_summary_key(user_id: int) -> str:
    return f"user:{user_id}:applications:summary"

def invalidate_user_application_summary(user_id: int) -> None:
    if redis_client is None:
        return  
    try:
        redis_client.delete(user_app_summary_key(user_id))
    except Exception as e:
        logger.warning("Failed to invalidate cache for user %s: %s", user_id, e)