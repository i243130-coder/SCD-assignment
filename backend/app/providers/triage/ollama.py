"""OllamaTriage provider for fully offline inference. Implemented in Phase 3."""

from app.providers.triage.base import TriageProvider, TriageResult


class OllamaTriage(TriageProvider):
    """Fully offline triage via local Ollama. Full implementation in Phase 3."""

    @property
    def name(self) -> str:
        return "llm:ollama"

    async def triage(self, text: str, location: str) -> TriageResult:
        raise NotImplementedError(
            "OllamaTriage is not yet implemented. Set TRIAGE_PROVIDER=simulated or rules."
        )
