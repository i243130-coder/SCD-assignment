"""Complaint CRUD routes."""

from uuid import UUID

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.middleware.rate_limiter import check_rate_limit
from app.providers.triage.factory import create_triage_provider
from app.redis_client import get_redis
from app.repositories.complaint_repo import ComplaintRepository
from app.schemas import (
    Category,
    ComplaintCreate,
    ComplaintListResponse,
    ComplaintResponse,
    PatchStatusRequest,
    Priority,
    Status,
)
from app.services.complaint_service import (
    ComplaintNotFoundError,
    ComplaintService,
    InvalidTransitionError,
)
from app.services.stats_service import StatsService

router = APIRouter(prefix="/api", tags=["complaints"])


@router.post("/complaints", response_model=ComplaintResponse, status_code=201)
async def create_complaint(
    data: ComplaintCreate,
    request: Request,
    session: AsyncSession = Depends(get_session),
    redis: aioredis.Redis = Depends(get_redis),
) -> ComplaintResponse:
    """Submit a new complaint. Triage is automatic."""
    await check_rate_limit(request, redis)

    repo = ComplaintRepository(session)
    provider = create_triage_provider(redis=redis)
    service = ComplaintService(repo, provider)
    stats_svc = StatsService(repo, redis)

    complaint = await service.create_complaint(data)
    await stats_svc.invalidate_cache()

    return ComplaintResponse.model_validate(complaint)


@router.get(
    "/complaints/{complaint_id}", response_model=ComplaintResponse
)
async def get_complaint(
    complaint_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> ComplaintResponse:
    """Fetch a single complaint by ID."""
    repo = ComplaintRepository(session)
    complaint = await repo.get_by_id(complaint_id)
    if complaint is None:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return ComplaintResponse.model_validate(complaint)


@router.get("/complaints", response_model=ComplaintListResponse)
async def list_complaints(
    category: Category | None = None,
    priority: Priority | None = None,
    status: Status | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> ComplaintListResponse:
    """List complaints with optional filters and pagination."""
    repo = ComplaintRepository(session)
    items, total = await repo.list_complaints(
        category=category,
        priority=priority,
        status=status,
        page=page,
        page_size=page_size,
    )
    return ComplaintListResponse(
        items=[ComplaintResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch(
    "/complaints/{complaint_id}/status",
    response_model=ComplaintResponse,
)
async def update_status(
    complaint_id: UUID,
    body: PatchStatusRequest,
    session: AsyncSession = Depends(get_session),
    redis: aioredis.Redis = Depends(get_redis),
) -> ComplaintResponse:
    """Update complaint status. Enforces state machine transitions."""
    repo = ComplaintRepository(session)
    provider = create_triage_provider(redis=redis)
    service = ComplaintService(repo, provider)
    stats_svc = StatsService(repo, redis)

    try:
        complaint = await service.update_status(
            complaint_id, body.status.value
        )
    except ComplaintNotFoundError:
        raise HTTPException(status_code=404, detail="Complaint not found")
    except InvalidTransitionError as exc:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot transition from '{exc.current}' to '{exc.requested}'",
        )

    await stats_svc.invalidate_cache()
    return ComplaintResponse.model_validate(complaint)
