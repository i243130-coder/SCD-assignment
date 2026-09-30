"""OpenTelemetry tracing: frontend -> backend -> LLM.

Tracing is opt-in. With OTEL_EXPORTER_OTLP_ENDPOINT unset (tests, CI, plain
`docker compose up`) nothing is installed and every span call below is a
cheap no-op, so behaviour stays deterministic.

When the endpoint is set:
- FastAPI server spans continue the browser's trace. The frontend sends a
  W3C `traceparent` header (frontend/src/tracing.ts), so one trace covers
  browser -> API.
- httpx client spans cover outbound calls. The Groq/OpenAI SDK uses httpx,
  so the LLM HTTP request is a child span automatically.
- Manual spans (`triage`, `llm.chat_completion`) carry the domain detail:
  provider, fallback, model and token usage.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from opentelemetry import trace

from app.config import settings

if TYPE_CHECKING:
    from fastapi import FastAPI
    from opentelemetry.sdk.trace import TracerProvider

logger = logging.getLogger(__name__)

# Probes, scrapes and the telemetry relay itself are not worth a trace each.
EXCLUDED_URLS = "/health,/ready,/metrics,/api/telemetry"

_provider: TracerProvider | None = None


def get_tracer(name: str) -> trace.Tracer:
    """Tracer bound to whatever provider is active (no-op when disabled)."""
    return trace.get_tracer(name)


def setup_tracing(app: FastAPI) -> bool:
    """Install OTLP export and auto-instrumentation. Returns True if enabled."""
    global _provider

    endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT.rstrip("/")
    if not endpoint:
        logger.info("Tracing disabled (OTEL_EXPORTER_OTLP_ENDPOINT not set)")
        return False
    if _provider is not None:
        return True

    # Imported lazily so the SDK is only loaded when tracing is on.
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    provider = TracerProvider(
        resource=Resource.create(
            {
                "service.name": settings.OTEL_SERVICE_NAME,
                "deployment.environment": settings.ENVIRONMENT,
            }
        )
    )
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{endpoint}/v1/traces")))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(app, tracer_provider=provider, excluded_urls=EXCLUDED_URLS)
    HTTPXClientInstrumentor().instrument(tracer_provider=provider)

    _provider = provider
    logger.info("Tracing enabled: exporting OTLP to %s", endpoint)
    return True


def shutdown_tracing() -> None:
    """Flush buffered spans on shutdown (called from the app lifespan)."""
    global _provider
    if _provider is not None:
        _provider.shutdown()
        _provider = None
