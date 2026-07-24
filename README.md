# SENTINEL — AI-Native Engineering Operations Platform

> One operational workspace that unifies log monitoring, deployment tracking, incident
> summarisation, task assignment, and AI-assisted debugging — replacing the fragmented
> Slack + Grafana + Jira + GitHub + Notion toolchain with one coherent, real-time,
> AI-native product.

**Problem statement:** Sentinel — AI Native Engineering Operations Platform (Hard).  
Brief: [ps.md](ps.md) · Architecture: [plan/ARCHITECTURE.md](plan/ARCHITECTURE.md) · Write-up: [WRITEUP.md](WRITEUP.md)

![status](https://img.shields.io/badge/tests-150%20passing-brightgreen)
![backend](https://img.shields.io/badge/backend-FastAPI-009688)
![frontend](https://img.shields.io/badge/frontend-Next.js%2015-black)
![deploy](https://img.shields.io/badge/deploy-Render%20%2B%20Vercel-blue)

| | URL |
|---|---|
| **GitHub** | https://github.com/Srujan0798/SENTINEL-HERS |
| **Live frontend (Vercel)** | _Set after deploy_ → `https://<your-app>.vercel.app` (see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)) |
| **Live backend (Render)** | _Set after deploy_ → `https://<your-service>.onrender.com` |
| **API health** | `https://<your-service>.onrender.com/healthz` |
| **OpenAPI** | `https://<your-service>.onrender.com/api/docs` |

> After you deploy, replace the two placeholder rows above with the real HTTPS URLs (submission requirement).

---

## Demo login (seeded)

| Field | Value |
|-------|--------|
| Email | `demo@sentinel.io` |
| Password | `Sentinel2026!` |

Sacred judge path: **Login → SEV1 dashboard → AI summary + root cause → assign/SLA → timeline → analytics**.  
Step-by-step: [docs/PRODUCTION_WALKTHROUGH.md](docs/PRODUCTION_WALKTHROUGH.md).

---

## What it does

| Capability | Status |
|------------|--------|
| Team auth + JWT + role-based access control | ✅ |
| Real-time incident dashboard (SEV1–4, triage, assignment, escalation) | ✅ |
| Centralised log + alert ingestion and search | ✅ |
| AI incident summaries + ranked root-cause suggestions | ✅ |
| GitHub / GitLab deployment + commit tracking (signed webhooks) | ✅ |
| Service health monitoring + Prometheus metrics | ✅ |
| Per-incident communication channels with @mentions | ✅ |
| Incident timeline with full event provenance | ✅ |
| Task assignment, escalation, SLA-aware workflow | ✅ |
| Analytics: MTTR, incident frequency, top errors, alert trends | ✅ |

**Exceptional / brownie features (code present — wave-10 hardens + proves):**  
Conversational RAG chatbot · Docker + Kubernetes monitoring · Auto-generated postmortems ·  
Voice-to-ticket · Predictive anomaly detection (IsolationForest).

---

## Architecture

```
┌──────────────────┐     SSE / WS      ┌─────────────────────────────┐
│  Next.js 15 UI   │ ◀───────────────▶ │       FastAPI backend        │
│  Tailwind/shadcn │   REST / JSON     │  auth · rbac · incidents     │
└──────────────────┘                   │  logs · ingest · comms       │
                                       │  ai (summary/rootcause/chat/ │
┌──────────────────┐                   │       postmortem) · tasks    │
│  Prometheus      │ ◀── /metrics ──── │  sla · analytics · ml        │
│  + Grafana       │                   │  integrations · voice        │
└──────────────────┘                   └──────────────┬──────────────┘
                                                       │
                              ┌────────────────────────┼───────────────┐
                              ▼                         ▼               ▼
                        PostgreSQL                   Redis        AI provider
                       (SQLite in tests)          (cache/pub-sub)  (Claude/Gemini/mock)
```

- **Shared SQLAlchemy Base** with portable column types → full suite on SQLite, no external services.
- **AI provider abstraction** (Claude / Gemini / deterministic mock) → live demo + offline tests.
- **Realtime hub** (SSE + WebSockets) for incident + comms fan-out.
- **Self-observing:** Prometheus metrics + Grafana assets ship in-repo.

Design: [plan/ARCHITECTURE.md](plan/ARCHITECTURE.md) · Product: [plan/PRD.md](plan/PRD.md) · Write-up: [WRITEUP.md](WRITEUP.md).

---

## Quick start (local)

```bash
cp .env.example .env          # set JWT_SECRET + JWT_REFRESH_SECRET (optional AI keys)
make up                       # postgres, redis, api, frontend, prometheus, grafana
make seed                     # SEV1 + logs + alerts + anomalies (idempotent)
open http://localhost:3000    # demo@sentinel.io / Sentinel2026!
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API + OpenAPI | http://localhost:8000 · http://localhost:8000/api/docs |
| Prometheus | http://localhost:9090 |
| Grafana (admin/admin) | http://localhost:3001 |

Full local paths: [HOW_TO_RUN.md](HOW_TO_RUN.md) · Cloud deploy: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

### Production env (minimum)

| Where | Variable | Notes |
|-------|----------|--------|
| Render | `ANTHROPIC_API_KEY` | dashboard-only secret |
| Render | `CORS_ORIGINS` | exact Vercel origin, e.g. `https://foo.vercel.app` |
| Vercel | `NEXT_PUBLIC_API_BASE_URL` | Render origin, no trailing slash |
| Vercel project | **Root Directory** | `src/frontend` |

---

## Tests

```bash
# from repo root, with venv active
python -m pytest -q          # full suite — currently 150 passed
```

**150 tests passing** (unit + integration; mock AI; SQLite). Verified after wave-9 hardening.

---

## Tech stack

| Layer | Choice |
|-------|--------|
| Frontend | Next.js 15, React 19, Tailwind, shadcn/ui |
| Backend | FastAPI (Python 3.11+), SQLAlchemy 2, Pydantic 2 |
| Database | PostgreSQL (prod) · SQLite (tests) |
| Realtime | Server-Sent Events + WebSockets |
| AI | Anthropic Claude / Google Gemini / mock provider |
| ML | scikit-learn (IsolationForest) |
| Observability | Prometheus + Grafana |
| Deploy | Docker · Render Blueprint · Vercel |

---

## Repository layout

```
api/              FastAPI entrypoint, startup migrations, requirements
src/backend/      Feature modules (auth, incidents, ai, comms, ml, …)
src/frontend/     Next.js app (Root Directory for Vercel)
tests/            unit + integration suites
deployment/       Prometheus, Grafana, Render release.sh
scripts/          seed_demo.py
plan/             PRD, ARCHITECTURE, EXECUTION tracker
work/             Task files + worker reports (orchestration)
docs/             Deployment, walkthrough, scope, security
WRITEUP.md        1–2 page technical write-up (submission required)
```

---

## Submission checklist

- [x] Public GitHub repo with meaningful commit history  
- [x] README with setup + demo path  
- [x] `WRITEUP.md` (technical decisions, challenges, more time)  
- [x] Green automated tests (150)  
- [x] Deploy configs (`render.yaml`, `src/frontend/vercel.json`)  
- [ ] Live deployment URLs embedded above (human: push + Render + Vercel)  
- [ ] Optional: wave-10 brownie harden via OpenCode agents (`work/OPENCODE_DISPATCH.md`)

Mid-term form drafts: [docs/SUBMISSION.md](docs/SUBMISSION.md).

> Built by Choda Srujan Sai (23110081) for METIS Summer Siege — dual-tier AI orchestration
> (see `plan/EXECUTION.md`, `work/DISPATCH.md`).
