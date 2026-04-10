import redis 

redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

def user_app_summary_key(user_id: int) -> str:
    return f"user:{user_id}:applications:summary"

def invalidate_user_application_summary(user_id: int) -> None:
    redis_client.delete(user_app_summary_key(user_id))