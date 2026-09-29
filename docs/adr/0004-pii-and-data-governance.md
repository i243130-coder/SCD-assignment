# ADR-0004: PII and Data Governance

## Status
Accepted

## Context
Groq free tier may use inputs for model improvement. Complaints contain PII (names, addresses, phones).

## Decision
Send only complaint text + location to LLM. Never send reporter_contact. Document exposure.

## Consequences
Reduced PII risk, slight loss of context for classification, compliant with reasonable data governance.
