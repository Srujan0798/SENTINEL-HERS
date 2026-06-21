# SENTINEL — AI-Native Engineering Operations Platform

> One operational workspace that unifies log monitoring, deployment tracking, incident
> summarisation, task assignment, and AI-assisted debugging — replacing the fragmented
> Slack + Grafana + Jira + GitHub + Notion toolchain with one coherent, real-time,
> AI-native product.

**Problem statement:** Sentinel — AI Native Engineering Operations Platform (Hard).
Full brief in [PROBLEM_STATEMENT.md](PROBLEM_STATEMENT.md).

![status](https://img.shields.io/badge/tests-146%20passing-brightgreen)
![backend](https://img.shields.io/badge/backend-FastAPI-009688)
![frontend](https://img.shields.io/badge/frontend-Next.js%2015-black)

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

**Exceptional features (all implemented):**
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

- **Shared SQLAlchemy Base** with portable column types → the full test suite runs on
  SQLite with no external services.
- **AI provider abstraction** (Claude / Gemini / deterministic mock) → graceful degradation
  and deterministic tests.
- **Realtime hub** (SSE + WebSockets, Redis-pub/sub ready) for incident + comms fan-out.
- **Self-observing**: the platform exposes its own Prometheus metrics and ships a Grafana
  dashboard + alert rules.

Design details: [plan/ARCHITECTURE.md](plan/ARCHITECTURE.md) · [plan/PRD.md](plan/PRD.md).

---

## Quick start

```bash
cp .env.example .env          # set JWT_SECRET + JWT_REFRESH_SECRET (and optional AI keys)
make up                       # postgres, redis, api, frontend, prometheus, grafana
make seed                     # realistic SEV1 incident + logs + alerts + anomalies
open http://localhost:3000    # login: demo@sentinel.io / Sentinel2026!
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API + OpenAPI docs | http://localhost:8000 · http://localhost:8000/api/docs |
| Prometheus | http://localhost:9090 |
| Grafana (admin/admin) | http://localhost:3001 |

Full instructions + local-dev (no Docker) path: [HOW_TO_RUN.md](HOW_TO_RUN.md).

---

## Tests

```bash
make test-fast    # ~15s, 134 tests (skips slow ML training)
make test-full    # full suite incl. IsolationForest training (146 tests)
```

**146 tests passing** across unit + integration (auth, RBAC, incidents, logs, AI, comms,
VCS, SLA, analytics, anomaly).

---

## Tech stack

| Layer | Choice |
|-------|--------|
| Frontend | Next.js 15, React 19, Tailwind, shadcn/ui |
| Backend | FastAPI (Python 3.11), SQLAlchemy 2, Pydantic 2 |
| Database | PostgreSQL (prod) · SQLite (tests) |
| Realtime | Server-Sent Events + WebSockets |
| AI | Anthropic Claude / Google Gemini / mock provider |
| ML | scikit-learn (IsolationForest) |
| Observability | Prometheus + Grafana |
| Deploy | Docker + Docker Compose |

---

## Repository layout

```
api/              FastAPI entrypoint (main.py), startup migrations, requirements
src/backend/      16 feature modules (auth, incidents, ai, comms, ml, …)
src/frontend/     Next.js app (app router, components, lib)
tests/            unit + integration suites
deployment/       Prometheus + Grafana provisioning
scripts/          seed_demo.py
plan/             PRD, ARCHITECTURE, EXECUTION tracker
docs/             SUBMISSION.md, scope, decisions, schemas
```

---

## Submission

Mid-term evaluation answers and the functional-requirement → code map:
[docs/SUBMISSION.md](docs/SUBMISSION.md).

> Built solo by Choda Srujan Sai (23110081) for METIS Summer Siege. The backend was
> developed wave-by-wave with an AI orchestration workflow (see `plan/EXECUTION.md`).
