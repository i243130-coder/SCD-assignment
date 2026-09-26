"""LLMTriage provider using Groq (OpenAI-compatible). Implemented in Phase 3."""

from app.providers.triage.base import TriageProvider, TriageResult


class LLMTriage(TriageProvider):
    """Production triage via hosted LLM (Groq). Full implementation in Phase 3."""

    @property
    def name(self) -> str:
        return "llm:groq"

    async def triage(self, text: str, location: str) -> TriageResult:
        raise NotImplementedError(
            "LLMTriage is not yet implemented. Set TRIAGE_PROVIDER=simulated or rules."
        )
