"""Health, readiness, and metrics endpoints."""

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response as StarletteResponse

from app.database import get_session
from app.redis_client import get_redis
from app.schemas import DependencyStatus, HealthResponse, ReadyResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness probe. Must NOT access database."""
    return HealthResponse(status="ok")


@router.get("/ready")
async def ready(
    response: Response,
    session: AsyncSession = Depends(get_session),
    redis: aioredis.Redis = Depends(get_redis),
) -> ReadyResponse:
    """Readiness probe. Checks PostgreSQL and Redis."""
    deps: list[DependencyStatus] = []
    all_healthy = True

    # Check PostgreSQL
    try:
        await session.execute(text("SELECT 1"))
        deps.append(DependencyStatus(name="postgresql", healthy=True))
    except Exception as exc:
        deps.append(
            DependencyStatus(
                name="postgresql", healthy=False, error=str(exc)
            )
        )
        all_healthy = False

    # Check Redis
    try:
        await redis.ping()
        deps.append(DependencyStatus(name="redis", healthy=True))
    except Exception as exc:
        deps.append(
            DependencyStatus(name="redis", healthy=False, error=str(exc))
        )
        all_healthy = False

    if not all_healthy:
        response.status_code = 503

    return ReadyResponse(
        status="ok" if all_healthy else "degraded",
        dependencies=deps,
    )


@router.get("/metrics")
async def metrics() -> StarletteResponse:
    """Prometheus metrics in text exposition format."""
    return StarletteResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
