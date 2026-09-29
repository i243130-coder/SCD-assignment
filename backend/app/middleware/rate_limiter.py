"""Redis-based distributed rate limiter using fixed-window with Lua script."""

from fastapi import HTTPException, Request
import redis.asyncio as aioredis

from app.config import settings

# Atomic Lua script for fixed-window rate limiting.
# Returns -1 if request is allowed, or the TTL (seconds until window resets) if denied.
RATE_LIMIT_SCRIPT = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])

local current = redis.call('INCR', key)
if current == 1 then
    redis.call('EXPIRE', key, window)
end

if current > limit then
    local ttl = redis.call('TTL', key)
    return ttl
end

return -1
"""


async def check_rate_limit(request: Request, redis: aioredis.Redis) -> None:
    """Check rate limit for POST /api/complaints. Raises 429 if exceeded."""
    client_ip = request.client.host if request.client else "unknown"
    key = f"rate_limit:{client_ip}"

    result = await redis.eval(  # type: ignore[attr-defined]
        RATE_LIMIT_SCRIPT,
        1,
        key,
        str(settings.RATE_LIMIT_MAX_REQUESTS),
        str(settings.RATE_LIMIT_WINDOW_SECONDS),
    )

    if result != -1:
        retry_after = max(int(result), 1)
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )
