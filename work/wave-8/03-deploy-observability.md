# TASK — wave-8 / 03-deploy-observability

## Goal
Production deployment hardening: Dockerfile multi-stage, docker-compose for full stack,
Prometheus rules for SLO alerts, Grafana dashboard JSON, CI smoke test.

## Context
- Wave: 8. Existing `Dockerfile.api`, `Dockerfile.frontend`, `docker-compose.yml` are
  skeleton. Need to be runnable end-to-end on a fresh machine.

## Write-set (ONLY these)
- Dockerfile.api (rewrite)
- Dockerfile.frontend (rewrite)
- docker-compose.yml (rewrite)
- deployment/prometheus/
- deployment/grafana/
- .github/workflows/ci.yml
- Makefile (extend with `make demo`, `make smoke`)

## Forbid-set
- src/**, scripts/seed_demo.py, plan/**

## Blast radius
r2 (builds docker images — confirm before pushing).

## Steps
1. **Dockerfile.api** (multi-stage):
   - Stage 1: install poetry/pip, copy requirements, install deps.
   - Stage 2: slim runtime, copy app, expose 8000, CMD uvicorn.
   - Health check via /healthz.
2. **Dockerfile.frontend** (multi-stage):
   - Stage 1: npm ci, npm run build.
   - Stage 2: copy .next + node_modules, expose 3000.
   - Use `output: "standalone"` in next.config.ts.
3. **docker-compose.yml** services:
   - postgres (or sqlite for dev)
   - redis
   - api (depends_on postgres + redis healthy)
   - frontend (depends_on api healthy)
   - prometheus (scrapes /metrics on api)
   - grafana (dashboards from /etc/grafana/provisioning)
4. **deployment/prometheus/prometheus.yml**: scrape api every 15s, alerting rules in
   `alerts.yml` for: high error rate, p99 latency, SEV1 incident rate, ML anomaly spike.
5. **deployment/grafana/dashboards/sentinel.json**: pre-built dashboard with panels for
   request rate, latency p50/p95/p99, error rate, active incidents, ML anomaly scores.
6. **.github/workflows/ci.yml**: on push, run pytest + frontend build + smoke.
7. **Makefile**: add `make demo` (build + up + seed), `make smoke` (run smoke test),
   `make down` (docker-compose down -v).

## Acceptance (PROOF — FM-09)
```
docker compose config
make demo
make smoke
# Expected: all services start, seed runs, smoke passes
```

## Report to
`work/reports/wave-8/03-deploy-observability.report.md`
