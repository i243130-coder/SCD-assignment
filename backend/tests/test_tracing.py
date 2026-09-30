"""OpenTelemetry tracing: browser relay endpoint and trace propagation.

Tracing is off in CI (no OTEL_EXPORTER_OTLP_ENDPOINT), so these tests use an
in-memory exporter and patch settings explicitly - nothing leaves the process.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from opentelemetry import context
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from app import tracing
from app.config import settings
from app.providers.triage.simulated import SimulatedTriage
from app.services import complaint_service
from app.services.complaint_service import ComplaintService

COLLECTOR = "http://collector.test:4318"
OTLP_JSON = b'{"resourceSpans": []}'
TRACE_ID = "4bf92f3577b34da6a3ce929d0e0e4736"
PARENT_SPAN_ID = "00f067aa0ba902b7"


# ── /api/telemetry/traces relay ──────────────────────────────


@pytest.mark.asyncio
async def test_relay_is_noop_when_tracing_disabled(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "OTEL_EXPORTER_OTLP_ENDPOINT", "")
    with patch("app.routes.telemetry._forward") as forward:
        response = await client.post(
            "/api/telemetry/traces", content=OTLP_JSON, headers={"Content-Type": "application/json"}
        )
    assert response.status_code == 204
    forward.assert_not_called()


@pytest.mark.asyncio
async def test_relay_forwards_otlp_to_collector(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "OTEL_EXPORTER_OTLP_ENDPOINT", COLLECTOR + "/")
    with patch("app.routes.telemetry._forward", return_value=True) as forward:
        response = await client.post(
            "/api/telemetry/traces", content=OTLP_JSON, headers={"Content-Type": "application/json"}
        )
    assert response.status_code == 202
    forward.assert_called_once_with(f"{COLLECTOR}/v1/traces", OTLP_JSON, "application/json")


@pytest.mark.asyncio
async def test_relay_reports_collector_failure(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "OTEL_EXPORTER_OTLP_ENDPOINT", COLLECTOR)
    with patch("app.routes.telemetry._forward", return_value=False):
        response = await client.post(
            "/api/telemetry/traces", content=OTLP_JSON, headers={"Content-Type": "application/json"}
        )
    assert response.status_code == 502


@pytest.mark.asyncio
async def test_relay_rejects_non_otlp_content_type(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "OTEL_EXPORTER_OTLP_ENDPOINT", COLLECTOR)
    with patch("app.routes.telemetry._forward") as forward:
        response = await client.post(
            "/api/telemetry/traces", content=b"hello", headers={"Content-Type": "text/plain"}
        )
    assert response.status_code == 415
    forward.assert_not_called()


@pytest.mark.asyncio
async def test_relay_rejects_oversized_body(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "OTEL_EXPORTER_OTLP_ENDPOINT", COLLECTOR)
    too_big = b"x" * (256 * 1024 + 1)
    with patch("app.routes.telemetry._forward") as forward:
        response = await client.post(
            "/api/telemetry/traces", content=too_big, headers={"Content-Type": "application/json"}
        )
    assert response.status_code == 413
    forward.assert_not_called()


@pytest.mark.asyncio
async def test_relay_rejects_empty_body(client: AsyncClient, monkeypatch):
    monkeypatch.setattr(settings, "OTEL_EXPORTER_OTLP_ENDPOINT", COLLECTOR)
    response = await client.post(
        "/api/telemetry/traces", content=b"", headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 400


# ── setup ─────────────────────────────────────────────────────


def test_setup_tracing_is_noop_without_endpoint(monkeypatch):
    monkeypatch.setattr(settings, "OTEL_EXPORTER_OTLP_ENDPOINT", "")
    assert tracing.setup_tracing(FastAPI()) is False


# ── propagation: browser traceparent -> backend triage span ──


@pytest.fixture
def exporter(monkeypatch):
    """Route the triage tracer to an in-memory exporter (no global provider)."""
    memory = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(memory))
    monkeypatch.setattr(complaint_service, "tracer", provider.get_tracer("test"))
    return memory


async def _triage_inside_incoming_trace(service: ComplaintService):
    """Run triage as if a request arrived with the browser's traceparent header."""
    incoming = TraceContextTextMapPropagator().extract({"traceparent": f"00-{TRACE_ID}-{PARENT_SPAN_ID}-01"})
    token = context.attach(incoming)
    try:
        return await service._triage_with_fallback("Water pipe burst near the main road", "Block 5")
    finally:
        context.detach(token)


@pytest.mark.asyncio
async def test_triage_span_continues_the_browser_trace(exporter):
    service = ComplaintService(AsyncMock(), SimulatedTriage())

    _, triaged_by = await _triage_inside_incoming_trace(service)

    [span] = [s for s in exporter.get_finished_spans() if s.name == "triage"]
    assert format(span.context.trace_id, "032x") == TRACE_ID
    assert format(span.parent.span_id, "016x") == PARENT_SPAN_ID
    assert span.attributes["triage.provider"] == "simulated"
    assert span.attributes["triage.fallback"] is False
    assert span.attributes["triage.triaged_by"] == triaged_by
    # PII guard: the complaint text must never be recorded on the span.
    assert all("Water pipe" not in str(v) for v in span.attributes.values())


@pytest.mark.asyncio
async def test_triage_span_records_fallback(exporter):
    service = ComplaintService(AsyncMock(), SimulatedTriage(should_fail=True))

    _, triaged_by = await _triage_inside_incoming_trace(service)

    [span] = [s for s in exporter.get_finished_spans() if s.name == "triage"]
    assert triaged_by == "rules:fallback"
    assert span.attributes["triage.fallback"] is True
    assert span.attributes["triage.triaged_by"] == "rules:fallback"
    assert any(event.name == "exception" for event in span.events)
