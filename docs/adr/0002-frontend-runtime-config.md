# ADR-0002: Frontend Runtime Config

## Status
Accepted

## Context
Frontend needs to call backend API. Can't bake env-specific URLs into Vite build.

## Decision
nginx /api proxy (not runtime /config.js).

## Consequences
Build-once-deploy-many, same image across environments, simpler than injecting config at runtime.
