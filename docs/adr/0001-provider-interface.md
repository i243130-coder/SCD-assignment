# ADR-0001: Provider Interface

## Status
Accepted

## Context
Need to support multiple AI triage backends (hosted LLM, local Ollama, rules, simulated).

## Decision
Strategy pattern with TriageProvider ABC, factory selection via env var.

## Consequences
Easy to add providers, CI deterministic with SimulatedTriage, fallback always available.
