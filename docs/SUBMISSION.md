# SENTINEL — METIS Hard Track Submission

## Live URLs
- **Frontend:** https://sentinel-hers.vercel.app
- **Backend:** https://sentinel-api-clu9.onrender.com
- **Demo login:** `demo@sentinel.io` / `Sentinel2026!`
- **API docs:** https://sentinel-api-clu9.onrender.com/api/docs
- **Metrics:** https://sentinel-api-clu9.onrender.com/metrics

## What is the progress till now? *

SENTINEL is a production-grade AI-native engineering operations platform. All 10 core functional requirements are implemented, deployed live, and verified. Current win-score: **~80%**.

**Backend (FastAPI, 16 modules, 47+ endpoints, 169 tests passing):**
- Team-based auth + JWT (access/refresh) with RBAC (ADMIN/OWNER/RESPONDER/VIEWER)
- Rate limiting on auth endpoints (login 10/min, register 5/min via slowapi)
- Incident lifecycle: severity (SEV1–4), status transitions, triage, assignment, **escalation**
- Centralised log + alert ingestion and search
- **Live AI** incident summaries (1,100+ chars via OpenRouter), ranked root-cause analysis (5 hypotheses), RAG chatbot with citations, auto-postmortems with Markdown download
- GitHub + GitLab webhooks (HMAC-verified in production)
- Service health monitoring + Prometheus `/metrics` (196 metric lines)
- Per-incident comms channels with SSE realtime fan-out
- Incident timeline with full event provenance
- Task assignment, escalation, SLA engine (SEV-based deadlines + breach detection)
- Analytics: MTTR, incidents-by-severity, top errors, alert trends, anomaly risk
- ML anomaly detection (IsolationForest pipeline)
- Docker + Kubernetes container monitoring (graceful fallback)
- Voice-to-ticket (speech → incident, auth from JWT)
- SSE realtime events on all lifecycle changes (incident.create/update/assign/escalate, task.create/update, sla.breach, health.change)
- 18 DB performance indexes + composite indexes for common queries
- Production boot checks (AI provider ≠ mock, JWT secrets required, ENV=production)
- CORS allow-list (no wildcard), WebSocket event ACL

**Frontend (Next.js 15 + React 19 + Tailwind/shadcn):** login/register, live dashboard with KPIs, incidents war room with AI Summary + RCA panels + timeline + tasks + comms + chat, monitoring (health + alerts), analytics, deployments. Deep-link via `/incidents?id=<uuid>`. Cold-start WakingOverlay. SSE StatusBar. Dark theme consistent (no light-theme leaks). Escalate dialog. Create task dialog.

**DevOps:** Docker Compose (postgres, redis, api, frontend, prometheus, grafana), GitHub Actions CI (pytest + tsc + build), Playwright sacred-path test (14 steps), `scripts/verify_live.sh` (15 live checks, all passing), Render deployment (ENV=production), Vercel deployment, idempotent migration script.

**Security (8 P0 fixes deployed):**
1. Voice auth from JWT (no client team_id injection)
2. Health auth + team filter
3. RBAC wired on all mutating routes
4. Webhook signatures required in production
5. Demo-status hides password in production
6. Task incident ownership check
7. WS event ACL (only channel:message/typing/pong)
8. JWT secrets refuse defaults in production + rate limiting

**Live verification (ALL PASSING):**
```
✓ /healthz → 200
✓ /api/demo-status → ready, 1 open SEV1, NO password leak
✓ /auth/login → JWT (rate limited 10/min)
✓ Unauth voice → 401
✓ Unauth health → 401
✓ Incidents → 3 total, SEV1 found
✓ AI Summary → 1,101 chars, NOT mock
✓ AI RCA → 5 hypotheses
✓ SSE → event: connected
✓ Escalate → 200
✓ Timeline/Tasks/SLA → 200
✓ Prometheus /metrics → 196 lines
✓ Frontend → live with WakingOverlay
```

## GitHub Repository

https://github.com/Srujan0798/SENTINEL-HERS

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, React 19, Tailwind CSS, shadcn/ui |
| Backend | FastAPI, Python 3.11, Uvicorn |
| Database | PostgreSQL 16 (Render Managed) |
| Realtime | SSE + WebSocket |
| AI | OpenRouter (Claude/Gemini/NVIDIA) |
| Auth | JWT (HS256), RBAC, bcrypt, rate limiting |
| Metrics | Prometheus (request latency, incident gauges, AI latency) |
| CI | GitHub Actions |
| Deploy | Render (backend), Vercel (frontend) |