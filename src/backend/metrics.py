"""Prometheus metrics for SENTINEL — request counts, latency, incident gauges."""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from fastapi.routing import APIRoute
import time

http_requests_total = Counter(
    "sentinel_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

http_request_duration_seconds = Histogram(
    "sentinel_http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

active_incidents = Gauge(
    "sentinel_active_incidents_total",
    "Number of open incidents by severity",
    ["severity"],
)

alerts_ingested_total = Counter(
    "sentinel_alerts_ingested_total",
    "Total alerts ingested",
    ["source", "severity"],
)

anomaly_scores = Histogram(
    "sentinel_anomaly_score",
    "ML anomaly scores by service",
    ["service"],
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)


async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start

    path = request.url.path
    # Bucket paths to avoid high cardinality from UUIDs
    for prefix in ["/api/incidents/", "/api/ai/incidents/", "/api/tasks/"]:
        if path.startswith(prefix) and len(path) > len(prefix):
            path = prefix + "{id}"
            break

    http_requests_total.labels(
        method=request.method,
        path=path,
        status=str(response.status_code),
    ).inc()
    http_request_duration_seconds.labels(
        method=request.method,
        path=path,
    ).observe(duration)

    return response


def metrics_endpoint():
    """Return Prometheus metrics in text format."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
