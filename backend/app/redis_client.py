"""Redis connection management."""

import redis.asyncio as aioredis

from app.config import settings

_redis_pool: aioredis.Redis | None = None


async def init_redis() -> None:
    """Initialize the global Redis connection pool."""
    global _redis_pool
    _redis_pool = aioredis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )


async def close_redis() -> None:
    """Close the Redis connection pool."""
    global _redis_pool
    if _redis_pool is not None:
        await _redis_pool.aclose()
        _redis_pool = None


async def get_redis() -> aioredis.Redis:
    """FastAPI dependency that returns the Redis client."""
    if _redis_pool is None:
        await init_redis()
    assert _redis_pool is not None
    return _redis_pool
