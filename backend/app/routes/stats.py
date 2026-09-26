"""Statistics endpoint with Redis cache."""

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.redis_client import get_redis
from app.repositories.complaint_repo import ComplaintRepository
from app.schemas import StatsResponse
from app.services.stats_service import StatsService

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    response: Response,
    session: AsyncSession = Depends(get_session),
    redis: aioredis.Redis = Depends(get_redis),
) -> dict:
    """Return aggregate stats. Uses 30s Redis read-through cache."""
    repo = ComplaintRepository(session)
    service = StatsService(repo, redis)
    stats, cache_hit = await service.get_stats()

    response.headers["X-Cache"] = "HIT" if cache_hit else "MISS"
    return stats
