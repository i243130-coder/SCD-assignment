"""Provider metadata endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.providers.triage.factory import create_triage_provider
from app.repositories.complaint_repo import ComplaintRepository
from app.schemas import ProviderInfoResponse

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/meta/providers", response_model=ProviderInfoResponse)
async def get_providers(
    session: AsyncSession = Depends(get_session),
) -> ProviderInfoResponse:
    """Active provider and last 20 triage outcomes."""
    provider = create_triage_provider()
    repo = ComplaintRepository(session)
    recent = await repo.get_recent_triages(limit=20)

    return ProviderInfoResponse(
        active_provider=provider.name,
        recent_triages=recent,  # type: ignore[arg-type]
    )
