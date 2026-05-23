import redis
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

def user_app_summary_key(user_id: int) -> str:
    return f"user:{user_id}:applications:summary"

def invalidate_user_application_summary(user_id: int) -> None:
    redis_client.delete(user_app_summary_key(user_id))