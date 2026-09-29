"""Complaint business logic — state machine, triage orchestration."""

import logging
import time
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.metrics import FALLBACK_COUNTER, TRIAGE_LATENCY
from app.models import Complaint
from app.providers.triage.base import TriageProvider, TriageResult
from app.providers.triage.rules import RuleBasedTriage
from app.repositories.complaint_repo import ComplaintRepository
from app.schemas import ComplaintCreate

logger = logging.getLogger(__name__)

# ── Explicit State Machine Transition Table ──────────────────
# Assignment requirement: "implement as an explicit transition table,
# not scattered if-statements."

VALID_TRANSITIONS: dict[str, set[str]] = {
    "open": {"in_progress", "rejected"},
    "in_progress": {"resolved", "rejected"},
    "resolved": set(),   # terminal
    "rejected": set(),   # terminal
}


class InvalidTransitionError(Exception):
    """Raised when a status transition violates the state machine."""

    def __init__(self, current: str, requested: str) -> None:
        self.current = current
        self.requested = requested
        super().__init__(
            f"Cannot transition from '{current}' to '{requested}'"
        )


class ComplaintNotFoundError(Exception):
    """Raised when a complaint ID does not exist."""

    def __init__(self, complaint_id: UUID) -> None:
        self.complaint_id = complaint_id
        super().__init__(f"Complaint {complaint_id} not found")


class ComplaintService:
    """Orchestrates complaint creation, retrieval, and status transitions."""

    def __init__(
        self,
        repo: ComplaintRepository,
        triage_provider: TriageProvider,
    ) -> None:
        self.repo = repo
        self.triage_provider = triage_provider
        self._fallback = RuleBasedTriage()

    async def create_complaint(self, data: ComplaintCreate) -> Complaint:
        """Validate, triage, persist, return."""
        start = time.monotonic()
        triage_result, triaged_by = await self._triage_with_fallback(
            data.text, data.location
        )
        latency_ms = int((time.monotonic() - start) * 1000)

        # Record triage latency metric
        TRIAGE_LATENCY.labels(provider=triaged_by).observe(
            latency_ms / 1000.0
        )

        complaint = Complaint(
            id=uuid4(),
            text=data.text,
            location=data.location,
            reporter_contact=data.reporter_contact,
            category=triage_result.category.value,
            priority=triage_result.priority.value,
            status="open",
            ai_summary=(
                triage_result.summary[:140] if triage_result.summary else None
            ),
            triaged_by=triaged_by,
            triage_latency_ms=latency_ms,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        return await self.repo.create(complaint)

    async def _triage_with_fallback(
        self, text: str, location: str
    ) -> tuple[TriageResult, str]:
        """Try the configured provider; fall back to rules on any failure."""
        try:
            result = await self.triage_provider.triage(text, location)
            return result, self.triage_provider.name
        except Exception:
            logger.warning(
                "Triage provider '%s' failed, falling back to rules",
                self.triage_provider.name,
                exc_info=True,
            )
            FALLBACK_COUNTER.inc()
            result = await self._fallback.triage(text, location)
            return result, "rules:fallback"

    async def get_complaint(self, complaint_id: UUID) -> Complaint:
        """Fetch a single complaint or raise."""
        complaint = await self.repo.get_by_id(complaint_id)
        if complaint is None:
            raise ComplaintNotFoundError(complaint_id)
        return complaint

    async def list_complaints(
        self, **kwargs: object
    ) -> tuple[list[Complaint], int]:
        """Delegate to repository with filters."""
        return await self.repo.list_complaints(**kwargs)  # type: ignore[arg-type]

    async def update_status(
        self, complaint_id: UUID, new_status: str
    ) -> Complaint:
        """Enforce state machine, then update."""
        complaint = await self.repo.get_by_id(complaint_id)
        if complaint is None:
            raise ComplaintNotFoundError(complaint_id)

        current = complaint.status
        allowed = VALID_TRANSITIONS.get(current, set())

        if new_status not in allowed:
            raise InvalidTransitionError(current, new_status)

        updated = await self.repo.update_status(complaint_id, new_status)
        if updated is None:
            raise ComplaintNotFoundError(complaint_id)
        return updated
