# CivicPulse

![CI Status](https://img.shields.io/github/actions/workflow/status/username/civicpulse/ci.yml?label=CI&style=flat-square) ![Coverage](https://img.shields.io/badge/coverage-80%25-green?style=flat-square)

## Problem Statement
Municipal complaint intake + AI triage platform.

## Architecture
```mermaid
flowchart LR
    Citizen -->|HTTP| React_Frontend[React Frontend]
    React_Frontend -->|REST API| FastAPI_Backend[FastAPI Backend]
    FastAPI_Backend -->|Triage Request| AI_Triage[AI Triage]
    FastAPI_Backend -->|Persist Data| PostgreSQL[(PostgreSQL)]
    FastAPI_Backend -->|Cache & Rate Limit| Redis[(Redis)]
```

## Quickstart
```bash
cp .env.example .env
docker compose up -d --build
# Wait for services, then:
docker compose exec backend alembic upgrade head
docker compose exec backend python -m scripts.seed
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/health
```

## API Endpoints (All 10 Endpoints)

| Method | Path | Behaviour / Contract |
|--------|------|----------------------|
| `POST` | `/api/complaints` | Validate → triage → persist. Returns `201 Created`. Field-level `400` validation error body. `429` with `Retry-After` header when rate limited. |
| `GET` | `/api/complaints/{id}` | Get complaint details (`200 OK` or `404 Not Found`). |
| `GET` | `/api/complaints` | Filter by `category`, `priority`, `status`; paginate (`page`, `page_size <= 100`); returns `{items, total, page, page_size}`. |
| `PATCH` | `/api/complaints/{id}/status` | Enforce explicit state machine table. Invalid transition returns `409 Conflict` naming attempted transition. |
| `GET` | `/api/stats` | Aggregates (by category & priority). Redis-cached with 30s TTL, returns `X-Cache: HIT` or `X-Cache: MISS`. Invalidated immediately on complaint creation. |
| `GET` | `/api/meta/providers` | Observability surface: active triage provider and last 20 triage outcomes (provider, latency ms, fallback flag). |
| `GET` | `/health` | Liveness probe for Kubernetes/Docker. Returns `{"status":"ok"}`. Process is alive; strictly does not touch the database. |
| `GET` | `/ready` | Readiness probe. `200 OK` only if PostgreSQL and Redis are both reachable; returns `503 Service Unavailable` naming the failed dependency. |
| `GET` | `/metrics` | Prometheus text exposition format: request count, request latency histogram, triage latency, and fallback counter. |
| `GET` | `/api/meta/config` | Runtime configuration information. |

## Technology Stack
- **Frontend**: React 18, Vite, TypeScript, Nginx (Alpine multi-stage build)
- **Backend**: FastAPI, Pydantic v2, SQLAlchemy 2 (asyncpg), Alembic
- **AI Triage Layer**: Groq (`llama-3.1-8b-instant`), Ollama (`llama3.2:1b`), Rule-based fallback, Deterministic simulated fake
- **Storage & Caching**: PostgreSQL 16 (persisted via `pgdata`), Redis 7 (AOF persistence, distributed rate limiting, and stats cache)
- **Containerization & Orchestration**: Docker Compose (multi-network, non-root), Kubernetes (Kustomize base & overlays, HPA v2, VPA, PDB)

## Project Structure

.
├── backend/
├── frontend/
├── k8s/
├── docs/
├── scripts/
├── compose.yaml
├── compose.prod.yaml
└── README.md
```

## Screenshots
*[Placeholder for screenshots of the application interface]*

## Documentation
- [AI Usage](docs/AI-USAGE.md)
- [Triage System](docs/TRIAGE.md)
- [Runbook](docs/RUNBOOK.md)
- [Engineering Notes](docs/ENGINEERING-NOTES.md)
- [Architecture Decision Records (ADRs)](docs/adr/)
- [Evidence](docs/evidence/README.md)
