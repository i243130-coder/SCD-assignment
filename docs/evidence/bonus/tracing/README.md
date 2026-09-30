# Evidence: OpenTelemetry tracing frontend → backend → LLM (+2)

Steps in [../README.md](../README.md#evidence-5-opentelemetry-frontend--backend--llm).

| File | What it shows |
|---|---|
| `jaeger-trace.png` | one trace spanning `civicpulse-frontend` → `civicpulse-backend` → `triage` → `llm.chat_completion` → HTTP call to Groq |
| `llm-span-attributes.png` | `gen_ai.*` attributes (model, token usage) on the LLM span |
| `jaeger-fallback.png` | a failed LLM call: `triage.fallback=true` + exception event |
| `jaeger-services.txt` | services known to Jaeger (from `ops/capture-bonus-evidence.ps1`) |
| `jaeger-recent-traces.txt` | recent frontend traces with their span chain |
