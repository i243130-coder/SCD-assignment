# ADR-0006: Metrics with Prometheus/Grafana, traces with OpenTelemetry

## Status
Accepted

## Context
`/metrics` existed but nothing scraped it, and a slow or failed complaint could not be followed across browser → API → triage → LLM.

## Decision
- **Metrics:** Prometheus in `k8s/observability` discovers backend **pods** (annotations `prometheus.io/*`), so each HPA replica is its own target. Grafana is provisioned from Git (datasources + the "CivicPulse - Backend" dashboard) with read-only anonymous access, so no password is committed.
- **Tracing:** OpenTelemetry, opt-in via `OTEL_EXPORTER_OTLP_ENDPOINT` (unset in CI, so tests stay deterministic). The backend uses the SDK with FastAPI and httpx auto-instrumentation plus manual `triage` and `llm.chat_completion` spans (GenAI attributes: model, token usage). The browser uses a zero-dependency module (`frontend/src/tracing.ts`) that sends a W3C `traceparent` and exports its CLIENT span as OTLP/JSON to a same-origin backend relay (`/api/telemetry/traces`), keeping the collector (Jaeger) off the public network with no CORS.
- **PII:** complaint text, prompts and completions are never span attributes (ADR-0004).

## Consequences
One trace shows where time goes, including the LLM call and whether the fallback fired. The relay is a public write endpoint, so it is capped at 256 KiB, accepts OTLP content types only, and is a no-op when tracing is off. Jaeger uses in-memory storage, which is fine for a demo but not durable.
