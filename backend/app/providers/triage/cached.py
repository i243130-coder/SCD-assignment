"""Cached triage provider wrapper — caches results by content hash in Redis.

Uses the Decorator pattern: wraps any TriageProvider transparently.
Cache key = SHA-256 of (text + location). TTL = 24 hours.
"""

import hashlib
import logging

import redis.asyncio as aioredis

from app.metrics import TRIAGE_CACHE_HITS, TRIAGE_CACHE_MISSES
from app.providers.triage.base import TriageProvider, TriageResult

logger = logging.getLogger(__name__)

TRIAGE_CACHE_PREFIX = "triage:cache:"
TRIAGE_CACHE_TTL = 86400  # 24 hours in seconds


class CachedTriageProvider(TriageProvider):
    """Wraps another provider with Redis content-hash caching.

    Duplicate complaints (e.g. nine neighbours reporting a burst main)
    cost one inference, not nine.
    """

    def __init__(self, wrapped: TriageProvider, redis: aioredis.Redis) -> None:
        self._wrapped = wrapped
        self._redis = redis

    @property
    def name(self) -> str:
        return self._wrapped.name

    @staticmethod
    def _cache_key(text: str, location: str) -> str:
        """Deterministic cache key from complaint content."""
        content = f"{text}:{location}"
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        return f"{TRIAGE_CACHE_PREFIX}{content_hash}"

    async def triage(self, text: str, location: str) -> TriageResult:
        """Check cache first; on miss, call wrapped provider and cache result."""
        key = self._cache_key(text, location)

        # Check cache
        try:
            cached = await self._redis.get(key)
            if cached is not None:
                TRIAGE_CACHE_HITS.inc()
                logger.debug("Triage cache HIT for key %s", key[:40])
                return TriageResult.model_validate_json(cached)
        except Exception:
            # If Redis is down, proceed without cache
            logger.warning("Redis cache read failed, proceeding without cache", exc_info=True)

        TRIAGE_CACHE_MISSES.inc()
        logger.debug("Triage cache MISS for key %s", key[:40])

        # Call wrapped provider (may raise — that's fine, caller handles fallback)
        result = await self._wrapped.triage(text, location)

        # Cache the result (best-effort, don't fail the request)
        try:
            await self._redis.setex(key, TRIAGE_CACHE_TTL, result.model_dump_json())
        except Exception:
            logger.warning("Redis cache write failed", exc_info=True)

        return result
