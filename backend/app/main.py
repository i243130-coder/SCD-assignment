"""FastAPI application factory."""

import logging
import time
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.metrics import REQUEST_COUNT, REQUEST_LATENCY
from app.middleware.request_id import RequestIDMiddleware
from app.redis_client import close_redis, init_redis
from app.routes import complaints, health, meta, stats, telemetry
from app.tracing import setup_tracing, shutdown_tracing

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup/shutdown lifecycle."""
    logger.info("Starting CivicPulse backend (provider=%s)", settings.TRIAGE_PROVIDER)
    await init_redis()
    yield
    logger.info("Shutting down CivicPulse backend")
    await close_redis()
    shutdown_tracing()


app = FastAPI(
    title="CivicPulse",
    description="Municipal complaint intake, triage, and operations platform",
    version="0.1.0",
    lifespan=lifespan,
)

# OpenTelemetry (no-op unless OTEL_EXPORTER_OTLP_ENDPOINT is set).
setup_tracing(app)

# ── Middleware ────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)


@app.middleware("http")
async def metrics_middleware(request: Request, call_next: object) -> object:
    """Track request count and latency for Prometheus."""
    start = time.monotonic()
    response = await call_next(request)  # type: ignore[misc]
    duration = time.monotonic() - start

    endpoint = request.url.path
    method = request.method
    status = str(response.status_code)  # type: ignore[union-attr]

    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

    return response  # type: ignore[return-value]


# ── Routes ────────────────────────────────────────────────────
app.include_router(complaints.router)
app.include_router(stats.router)
app.include_router(meta.router)
app.include_router(health.router)
app.include_router(telemetry.router)
