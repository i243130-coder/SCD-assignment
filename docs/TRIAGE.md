# Triage System

## Provider Interface Design
The triage system uses a strategy pattern with a `TriageProvider` abstract base class. Four providers implement this interface:
- **LLMTriage**: Uses Groq LLM API.
- **OllamaTriage**: Uses a local Ollama instance for LLM triage.
- **RuleBasedTriage**: Uses simple rules to categorize complaints.
- **SimulatedTriage**: Deterministic mock triage for testing and CI.

Provider selection is controlled via the `TRIAGE_PROVIDER` environment variable.

## Retry Strategy
- Timeout: 10s.
- Retry: Once with jitter on timeout, 429, or 5xx errors.
- Never retry on 400 errors.

## Fallback Chain
Primary Provider → `RuleBasedTriage` with `triaged_by='rules:fallback'`

## Content Hash Caching
- Key: SHA-256 of text + location.
- TTL: 24 hours in Redis.
- Purpose: Prevent redundant LLM calls for identical complaints.

## Prompt Injection Protection
- XML delimiters to separate instructions from user input.
- Constrained output (e.g., using JSON schema).
- Pydantic validation for the response.

## PII Handling
Only `text` and `location` are sent to the LLM. The `reporter_contact` is **never** sent to the AI providers.

## Cache Recovery: AOF Persistence
- **Why it is useful**: AOF (Append Only File) helps Redis recover rate-limit counters and triage cache on restart. For the triage cache (24h TTL), this avoids re-calling the LLM after a Redis restart. For rate limiting, AOF preserves window counters (prevents exploit by restarting Redis).
- **Trade-off**: AOF adds disk I/O, slightly slower than RDB-only.
- **Conclusion**: For this application, the cost is worth it for rate limit integrity.
