"""Triage provider interface and result model."""

from abc import ABC, abstractmethod

from pydantic import BaseModel, Field

from app.schemas import Category, Priority


class TriageResult(BaseModel):
    """Result of AI triage classification."""

    category: Category
    priority: Priority
    summary: str = Field(max_length=140)
    confidence: float = Field(ge=0.0, le=1.0)


class TriageProvider(ABC):
    """Abstract base class for triage providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier for triaged_by field."""
        ...

    @abstractmethod
    async def triage(self, text: str, location: str) -> TriageResult:
        """Classify a complaint and return triage result."""
        ...
