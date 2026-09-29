"""Pydantic v2 request/response schemas."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ── Domain Enums ──────────────────────────────────────────────


class Category(str, Enum):
    WATER = "water"
    ELECTRICITY = "electricity"
    SANITATION = "sanitation"
    ROADS = "roads"
    STREETLIGHTS = "streetlights"
    OTHER = "other"


class Priority(str, Enum):
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class Status(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    REJECTED = "rejected"


# ── Request Schemas ───────────────────────────────────────────


class ComplaintCreate(BaseModel):
    """Citizen complaint submission."""

    text: str = Field(..., min_length=10, max_length=2000)
    location: str = Field(..., min_length=3, max_length=200)
    reporter_contact: str | None = Field(default=None, max_length=200)


class PatchStatusRequest(BaseModel):
    """Status update request."""

    status: Status


# ── Response Schemas ──────────────────────────────────────────


class ComplaintResponse(BaseModel):
    """Single complaint response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    text: str
    location: str
    reporter_contact: str | None
    category: str
    priority: str
    status: str
    ai_summary: str | None
    triaged_by: str
    triage_latency_ms: int
    created_at: datetime
    updated_at: datetime


class ComplaintListResponse(BaseModel):
    """Paginated complaint list."""

    items: list[ComplaintResponse]
    total: int
    page: int
    page_size: int


# ── Stats Schemas ─────────────────────────────────────────────


class CategoryStats(BaseModel):
    category: str
    count: int


class PriorityStats(BaseModel):
    priority: str
    count: int


class StatsResponse(BaseModel):
    categories: list[CategoryStats]
    priorities: list[PriorityStats]
    total: int


# ── Health Schemas ────────────────────────────────────────────


class DependencyStatus(BaseModel):
    name: str
    healthy: bool
    error: str | None = None


class HealthResponse(BaseModel):
    status: str


class ReadyResponse(BaseModel):
    status: str
    dependencies: list[DependencyStatus]


# ── Provider Meta Schemas ─────────────────────────────────────


class TriageOutcome(BaseModel):
    provider: str
    latency_ms: int
    fallback: bool
    created_at: datetime


class ProviderInfoResponse(BaseModel):
    active_provider: str
    recent_triages: list[TriageOutcome]
