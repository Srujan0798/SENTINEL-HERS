# TASK — wave-3 / 02-service-health

## Goal
Service health monitoring with uptime probes, Prometheus metrics export, and realtime status updates.

## Context
- Wave: 3. Schema: `service_health` table. Prometheus config at `config/prometheus.yml`.

## Write-set (ONLY these)
- src/backend/health/
- config/prometheus.yml (extend existing)

## Forbid-set
- src/backend/logs/, frontend/**, docker-compose.yml (frozen from wave-0)

## Blast radius
r1.

## Steps
1. SQLAlchemy model for `ServiceHealth` (service_name, status: healthy/degraded/down, last_check, uptime_pct, latency_ms, metadata).
2. `GET /api/health/services` — list all services with current status.
3. `POST /api/health/services` — register a service for monitoring.
4. Background probe task (APScheduler or asyncio): ping each service every 30s, record result, emit `service.health_changed` to realtime hub on status change.
5. Prometheus: expose `/metrics` with `sentinel_service_uptime_ratio` + `sentinel_service_latency_ms` gauges per service.
6. Update `config/prometheus.yml` scrape config to include the api service /metrics endpoint.

## Acceptance (PROOF — FM-09)
```
pytest tests/integration/test_health.py -v
# Expected: register service, probe recorded, status changes trigger realtime event, /metrics returns valid Prometheus format
```

## Report to
`work/reports/wave-3/02-service-health.report.md`
