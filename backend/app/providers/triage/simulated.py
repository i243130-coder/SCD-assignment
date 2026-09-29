"""Deterministic fake provider for CI. Seeded, no network, configurable failure."""

import hashlib

from app.providers.triage.base import TriageProvider, TriageResult
from app.schemas import Category, Priority


class SimulatedTriage(TriageProvider):
    """Deterministic fake for CI — uses content hash for stable, repeatable results."""

    def __init__(self, *, should_fail: bool = False) -> None:
        self._should_fail = should_fail

    @property
    def name(self) -> str:
        return "simulated"

    async def triage(self, text: str, location: str) -> TriageResult:
        if self._should_fail:
            raise RuntimeError("SimulatedTriage configured to fail")

        # Deterministic: hash content to pick category/priority
        content_hash = hashlib.sha256(f"{text}:{location}".encode()).hexdigest()
        hash_int = int(content_hash[:8], 16)

        categories = list(Category)
        priorities = list(Priority)

        category = categories[hash_int % len(categories)]
        priority = priorities[(hash_int >> 8) % len(priorities)]

        summary = f"[Simulated] Issue reported at {location[:50]}"
        if len(summary) > 140:
            summary = summary[:137] + "..."

        return TriageResult(
            category=category,
            priority=priority,
            summary=summary,
            confidence=0.85,
        )
