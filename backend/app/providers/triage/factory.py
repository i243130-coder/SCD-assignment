"""Factory for creating the configured triage provider."""

import logging

from app.config import settings
from app.providers.triage.base import TriageProvider

logger = logging.getLogger(__name__)

# Singleton cache
_provider: TriageProvider | None = None


def create_triage_provider() -> TriageProvider:
    """Create and cache a triage provider based on TRIAGE_PROVIDER setting."""
    global _provider
    if _provider is not None:
        return _provider

    provider_name = settings.TRIAGE_PROVIDER.lower().strip()
    logger.info("Initializing triage provider: %s", provider_name)

    if provider_name == "simulated":
        from app.providers.triage.simulated import SimulatedTriage

        _provider = SimulatedTriage()
    elif provider_name == "rules":
        from app.providers.triage.rules import RuleBasedTriage

        _provider = RuleBasedTriage()
    elif provider_name == "llm":
        from app.providers.triage.llm import LLMTriage

        _provider = LLMTriage()
    elif provider_name == "ollama":
        from app.providers.triage.ollama import OllamaTriage

        _provider = OllamaTriage()
    else:
        raise ValueError(f"Unknown triage provider: {provider_name!r}")

    return _provider


def reset_provider() -> None:
    """Reset the cached provider (useful for testing)."""
    global _provider
    _provider = None
