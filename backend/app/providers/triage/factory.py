"""Factory for creating the configured triage provider.

The base provider is a singleton (created once from TRIAGE_PROVIDER env var).
When Redis is available, the factory wraps it with CachedTriageProvider
for content-hash deduplication (24h TTL).
"""

import logging

import redis.asyncio as aioredis

from app.config import settings
from app.providers.triage.base import TriageProvider

logger = logging.getLogger(__name__)

# Singleton cache for the base (uncached) provider
_base_provider: TriageProvider | None = None


def _create_base_provider() -> TriageProvider:
    """Create the base triage provider from TRIAGE_PROVIDER setting."""
    provider_name = settings.TRIAGE_PROVIDER.lower().strip()
    logger.info("Initializing triage provider: %s", provider_name)

    if provider_name == "simulated":
        from app.providers.triage.simulated import SimulatedTriage

        return SimulatedTriage()
    elif provider_name == "rules":
        from app.providers.triage.rules import RuleBasedTriage

        return RuleBasedTriage()
    elif provider_name == "llm":
        from app.providers.triage.llm import LLMTriage

        return LLMTriage()
    elif provider_name == "ollama":
        from app.providers.triage.ollama import OllamaTriage

        return OllamaTriage()
    else:
        raise ValueError(f"Unknown triage provider: {provider_name!r}")


def create_triage_provider(
    redis: aioredis.Redis | None = None,
) -> TriageProvider:
    """Get or create the triage provider, optionally wrapped with cache.

    The base provider is a singleton. The CachedTriageProvider wrapper
    is lightweight (two references) and created per-call when Redis
    is provided — this is fine because it delegates all real work to
    the cached singleton.
    """
    global _base_provider
    if _base_provider is None:
        _base_provider = _create_base_provider()

    if redis is not None:
        from app.providers.triage.cached import CachedTriageProvider

        return CachedTriageProvider(_base_provider, redis)

    return _base_provider


def reset_provider() -> None:
    """Reset the cached provider (useful for testing)."""
    global _base_provider
    _base_provider = None
