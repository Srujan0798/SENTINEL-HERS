# SENTINEL — AI-Native Engineering Operations Platform

[![Tests](https://github.com/Srujan0798/SENTINEL-HERS/actions/workflows/ci.yml/badge.svg)](https://github.com/Srujan0798/SENTINEL-HERS/actions)
[![Frontend](https://img.shields.io/badge/frontend-sentinel--hers.vercel.app-blue)](https://sentinel-hers.vercel.app)
[![Backend](https://img.shields.io/badge/backend-sentinel--api--clu9.onrender.com-green)](https://sentinel-api-clu9.onrender.com/healthz)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> One operational workspace that unifies log monitoring, deployment tracking, incident
> summarisation, task assignment, and AI-assisted debugging — replacing the fragmented
> Slack + Grafana + Jira + GitHub + Notion toolchain with one coherent, real-time,
> AI-native product.

**Problem statement:** Sentinel — AI Native Engineering Operations Platform (Hard).  
Brief: [ps.md](ps.md) · Architecture: [plan/ARCHITECTURE.md](plan/ARCHITECTURE.md) · Write-up: [WRITEUP.md](WRITEUP.md)

![status](https://img.shields.io/badge/tests-198%20passing-brightgreen)
![backend](https://img.shields.io/badge/backend-FastAPI-009688)
![frontend](https://img.shields.io/badge/frontend-Next.js%2015-black)
![deploy](https://img.shields.io/badge/deploy-Render%20%2B%20Vercel-blue)

| | URL |
|---|---|
| **GitHub** | https://github.com/Srujan0798/SENTINEL-HERS |
| **Live frontend (Vercel)** | `https://sentinel-hers.vercel.app` |
| **Live backend (Render)** | `https://sentinel-api-clu9.onrender.com` |
| **API health** | `https://sentinel-api-clu9.onrender.com/healthz` |
| **OpenAPI** | `https://sentinel-api-clu9.onrender.com/api/docs` |

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

| Capability | Status | Notes |
|------------|--------|-------|
| Team auth + JWT + role-based access control | ✅ DONE | Login, register, refresh, RBAC wired |
| Real-time incident dashboard (SEV1–4, triage, assignment, escalation) | ✅ DONE | Full war room with SLA timer |
| Centralised log + alert ingestion and search | ✅ DONE | Alert monitoring surface |
| AI incident summaries + ranked root-cause suggestions | ✅ DONE | Real OpenRouter LLM — live summaries + 5 root-cause hypotheses |
| GitHub / GitLab deployment + commit tracking (signed webhooks) | ✅ DONE | Webhook endpoints, deployment listing |
| Service health monitoring + Prometheus metrics | ✅ DONE | Health dashboard + /metrics |
| Per-incident communication channels with @mentions | ✅ DONE | Live chat in war room |
| Incident timeline with full event provenance | ✅ DONE | 4 timeline events per incident (detection → ack → investigation → mitigation) |
| Task assignment, escalation, SLA-aware workflow | ✅ DONE | Tasks with priorities, checkboxes, SLA breach tracking |
| Analytics: MTTR, incident frequency, top errors, alert trends | ✅ DONE | Dashboard + analytics page with predictive anomaly risk |
| Realtime SSE + WebSockets | ✅ DONE | Live status indicators |
| Predictive anomaly (IsolationForest) | ✅ DONE | 4 services monitored with anomaly risk scores |

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
| Render | `NVAPI_KEY` | NVIDIA API key (primary AI provider) |
| Render | `AI_PROVIDER` | `nvidia` (primary), falls back to `openrouter` → `claude` → `gemini` |
| Render | `CORS_ORIGINS` | exact Vercel origin, e.g. `https://foo.vercel.app` |
| Render | `ENCRYPTION_KEY` | Fernet key for AI settings at rest |
| Render | `ENABLE_HEALTH_PROBER` | `1` to enable health-check prober |
| Vercel | `NEXT_PUBLIC_API_BASE_URL` | Render origin, no trailing slash |
| Vercel project | **Root Directory** | `src/frontend` |

---

## Tests

```bash
# from repo root, with venv active
python -m pytest -q          # full suite — currently 198 passed
```

**198 tests passing** (unit + integration; mock AI; SQLite). Verified end-to-end in browser with live Render + Vercel.

---

## Tech stack

| Layer | Choice |
|-------|--------|
| Frontend | Next.js 15, React 19, Tailwind, shadcn/ui |
| Backend | FastAPI (Python 3.11+), SQLAlchemy 2, Pydantic 2 |
| Database | PostgreSQL 16 + **pgvector** (prod) · SQLite (tests) |
| Realtime | Server-Sent Events + WebSockets + **Redis pub/sub** |
| AI | **NVIDIA NIM** (primary) / OpenRouter / Claude / Gemini / Mock provider |
| ML | scikit-learn (IsolationForest anomaly detection) |
| Vector Search | **pgvector** — 768-dim embeddings via NVIDIA embedding API |
| VCS | GitHub + **GitLab** webhooks (push, MR, pipeline, deployment) |
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
- [x] Green automated tests (183)  
- [x] Deploy configs (`render.yaml`, `src/frontend/vercel.json`)  
- [x] Live deployment URLs embedded above  
- [x] Verified end-to-end in browser — login → dashboard → SEV1 war room → AI → analytics  
- [x] AI key persisted to DB — survives Render restarts without dashboard env vars

> Built by Choda Srujan Sai (23110081) for METIS Summer Siege — dual-tier AI orchestration
> (see `plan/EXECUTION.md`, `work/DISPATCH.md`).
