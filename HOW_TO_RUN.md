# HOW TO RUN — SENTINEL

## Quick start (Docker Compose — recommended)

```bash
# 1. Copy env and fill in secrets
cp .env.example .env
# Edit .env: set JWT_SECRET, JWT_REFRESH_SECRET, and optionally ANTHROPIC_API_KEY

# 2. Start everything
make up
# Brings up: postgres, redis, api (port 8000), frontend (port 3000),
#            prometheus (port 9090), grafana (port 3001)

# 3. Seed demo data
make seed
# Creates demo@sentinel.io / Sentinel2026! with a realistic SEV1 incident

# 4. Open the app
open http://localhost:3000
# Login: demo@sentinel.io / Sentinel2026!
```

## Services at a glance

| Service | URL | Notes |
|---------|-----|-------|
| Frontend | http://localhost:3000 | Next.js 15 dashboard |
| API | http://localhost:8000 | FastAPI, auto-docs at /api/docs |
| Prometheus | http://localhost:9090 | Scrapes /metrics every 15s |
| Grafana | http://localhost:3001 | admin/admin, SENTINEL dashboard pre-loaded |

## Local dev (no Docker)

```bash
# Backend
pip install -r api/requirements.txt
export DATABASE_URL=sqlite:///./sentinel.db
export JWT_SECRET=local-dev-secret-32chars!!!!!
export JWT_REFRESH_SECRET=local-dev-refresh-32chars!!!!
export AI_PROVIDER=mock        # or claude / gemini with API key
uvicorn api.main:app --reload --port 8000

# Frontend (separate terminal)
cd src/frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

## Run tests

```bash
# All tests (fast — ~15s)
python3 -m pytest tests/ --ignore=tests/performance --ignore=tests/integration/test_anomaly.py -q

# Including slow ML test (~5 min, trains IsolationForest)
python3 -m pytest tests/ --ignore=tests/performance -q

# Single module
python3 -m pytest tests/integration/test_incidents.py -v
```

Expected: **146 tests passing, 0 failures**.

## Demo path (the thing judges care about)

1. **Login** → `demo@sentinel.io` / `Sentinel2026!`
2. **Dashboard** → see live KPIs: open incidents, MTTR, anomaly count
3. **Incidents** → click the SEV1 "Payment service cascade failure"
4. **AI Summary** → auto-generated 3-paragraph summary appears
5. **Root Cause** → ranked list with confidence scores
6. **Analytics** → MTTR trends, severity breakdown, top error messages
7. **Monitoring** → live container health, active alerts
8. **API docs** → http://localhost:8000/api/docs (full OpenAPI spec, 47 endpoints)
9. **Metrics** → http://localhost:8000/metrics (Prometheus scrape target)
10. **Grafana** → http://localhost:3001 → SENTINEL Operations dashboard

## Makefile targets

```
make up      # docker compose up --build -d
make down    # docker compose down
make build   # docker compose build (no start)
make logs    # docker compose logs -f
make test    # pytest inside api container
make seed    # run scripts/seed_demo.py against localhost:8000
```
