"""
Redis connection and dependency for FastAPI
"""
import redis.asyncio as redis
from src.core.config import settings

# Redis client instance
redis_client: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    """
    Dependency to get Redis client connection.

    Returns:
        Redis client instance
    """
    global redis_client

    if redis_client is None:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )

    return redis_client


async def close_redis():
    """Close Redis connection on application shutdown"""
    global redis_client

    if redis_client:
        await redis_client.close()
        redis_client = None
