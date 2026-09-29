"""Statistics service with Redis read-through cache."""

import json
import logging

import redis.asyncio as aioredis

from app.repositories.complaint_repo import ComplaintRepository

logger = logging.getLogger(__name__)

STATS_CACHE_KEY = "civicpulse:stats"
STATS_CACHE_TTL = 30  # seconds


class StatsService:
    """Aggregates stats with a 30-second Redis read-through cache."""

    def __init__(
        self, repo: ComplaintRepository, redis: aioredis.Redis
    ) -> None:
        self.repo = repo
        self.redis = redis

    async def get_stats(self) -> tuple[dict, bool]:
        """
        Returns (stats_dict, cache_hit).
        cache_hit=True means the data came from Redis, not the database.
        """
        cached = await self.redis.get(STATS_CACHE_KEY)
        if cached is not None:
            return json.loads(cached), True

        stats = await self.repo.get_stats()
        await self.redis.setex(
            STATS_CACHE_KEY, STATS_CACHE_TTL, json.dumps(stats)
        )
        return stats, False

    async def invalidate_cache(self) -> None:
        """Delete the stats cache. Called after any complaint write."""
        await self.redis.delete(STATS_CACHE_KEY)
