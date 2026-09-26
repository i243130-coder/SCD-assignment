"""Prometheus metrics definitions."""

from prometheus_client import Counter, Histogram

# HTTP metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)

# Triage metrics
TRIAGE_LATENCY = Histogram(
    "triage_duration_seconds",
    "Triage provider latency in seconds",
    ["provider"],
)

FALLBACK_COUNTER = Counter(
    "triage_fallback_total",
    "Total number of triage fallbacks to RuleBasedTriage",
)

TRIAGE_CACHE_HITS = Counter(
    "triage_cache_hits_total",
    "Total triage cache hits",
)

TRIAGE_CACHE_MISSES = Counter(
    "triage_cache_misses_total",
    "Total triage cache misses",
)
