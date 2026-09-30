"""Same-origin relay for browser traces.

The browser cannot reach the OTLP collector directly: it lives on an internal
network with no Ingress, and exposing it would mean opening CORS on a
write endpoint. The frontend therefore POSTs OTLP/JSON to /api/telemetry/traces
(same origin, already proxied by nginx), and the backend forwards it to the
collector configured in OTEL_EXPORTER_OTLP_ENDPOINT.

Guard rails: tracing off -> 204 and nothing is forwarded; only OTLP content
types; bodies capped at 256 KiB; the forward uses urllib (not httpx) so the
relay does not create spans about itself.
"""

import asyncio
import logging
import urllib.error
import urllib.request

from fastapi import APIRouter, Request, Response

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/telemetry", tags=["telemetry"])

MAX_BODY_BYTES = 256 * 1024
ALLOWED_CONTENT_TYPES = {"application/json", "application/x-protobuf"}
FORWARD_TIMEOUT_SECONDS = 3


def _forward(url: str, body: bytes, content_type: str) -> bool:
    """POST the OTLP payload to the collector. Runs in a worker thread."""
    req = urllib.request.Request(url, data=body, method="POST", headers={"Content-Type": content_type})
    try:
        with urllib.request.urlopen(req, timeout=FORWARD_TIMEOUT_SECONDS) as resp:  # noqa: S310 - URL from config
            return 200 <= resp.status < 300
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        logger.warning("Trace relay to collector failed: %s", exc)
        return False


@router.post("/traces", status_code=202)
async def relay_traces(request: Request) -> Response:
    """Forward browser spans (OTLP/HTTP) to the collector."""
    endpoint = settings.OTEL_EXPORTER_OTLP_ENDPOINT.rstrip("/")
    if not endpoint:
        return Response(status_code=204)

    content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        return Response(status_code=415)

    declared = request.headers.get("content-length", "")
    if declared.isdigit() and int(declared) > MAX_BODY_BYTES:
        return Response(status_code=413)

    body = await request.body()
    if not body:
        return Response(status_code=400)
    if len(body) > MAX_BODY_BYTES:
        return Response(status_code=413)

    ok = await asyncio.to_thread(_forward, f"{endpoint}/v1/traces", body, content_type)
    return Response(status_code=202 if ok else 502)
