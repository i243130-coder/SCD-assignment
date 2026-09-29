"""Complaint repository — all database queries live here."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Complaint
from app.schemas import Category, Priority, Status


class ComplaintRepository:
    """Data access layer for complaints. No business logic."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, complaint: Complaint) -> Complaint:
        """Insert a new complaint."""
        self.session.add(complaint)
        await self.session.commit()
        await self.session.refresh(complaint)
        return complaint

    async def get_by_id(self, complaint_id: UUID) -> Complaint | None:
        """Fetch a single complaint by ID."""
        return await self.session.get(Complaint, complaint_id)

    async def list_complaints(
        self,
        category: Category | None = None,
        priority: Priority | None = None,
        status: Status | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Complaint], int]:
        """Paginated listing with optional filters."""
        query = select(Complaint)
        count_query = select(func.count()).select_from(Complaint)

        if category is not None:
            query = query.where(Complaint.category == category.value)
            count_query = count_query.where(Complaint.category == category.value)
        if priority is not None:
            query = query.where(Complaint.priority == priority.value)
            count_query = count_query.where(Complaint.priority == priority.value)
        if status is not None:
            query = query.where(Complaint.status == status.value)
            count_query = count_query.where(Complaint.status == status.value)

        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        query = query.order_by(Complaint.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.session.execute(query)
        complaints = list(result.scalars().all())

        return complaints, total

    async def update_status(
        self, complaint_id: UUID, new_status: str
    ) -> Complaint | None:
        """Update the status of an existing complaint."""
        complaint = await self.get_by_id(complaint_id)
        if complaint is None:
            return None
        complaint.status = new_status
        complaint.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(complaint)
        return complaint

    async def get_stats(self) -> dict:
        """Aggregate counts by category and priority."""
        # Category counts
        cat_query = select(
            Complaint.category, func.count().label("count")
        ).group_by(Complaint.category)
        cat_result = await self.session.execute(cat_query)
        categories = [
            {"category": row.category, "count": row.count}
            for row in cat_result.all()
        ]

        # Priority counts
        pri_query = select(
            Complaint.priority, func.count().label("count")
        ).group_by(Complaint.priority)
        pri_result = await self.session.execute(pri_query)
        priorities = [
            {"priority": row.priority, "count": row.count}
            for row in pri_result.all()
        ]

        # Total
        total_query = select(func.count()).select_from(Complaint)
        total = (await self.session.execute(total_query)).scalar() or 0

        return {
            "categories": categories,
            "priorities": priorities,
            "total": total,
        }

    async def get_recent_triages(self, limit: int = 20) -> list[dict]:
        """Get the most recent triage outcomes for /api/meta/providers."""
        query = (
            select(
                Complaint.triaged_by,
                Complaint.triage_latency_ms,
                Complaint.created_at,
            )
            .order_by(Complaint.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return [
            {
                "provider": row.triaged_by,
                "latency_ms": row.triage_latency_ms,
                "fallback": "fallback" in (row.triaged_by or ""),
                "created_at": row.created_at.isoformat(),
            }
            for row in result.all()
        ]
