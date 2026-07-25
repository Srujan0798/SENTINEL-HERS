# SENTINEL — AI-Native Engineering Operations Platform

## METIS Hard Track — Technical Writeup

### Overview

SENTINEL is an AI-native engineering operations platform that unifies log monitoring, deployment tracking, incident summarisation, task assignment, and AI-assisted debugging into a single operational workspace. It replaces the fragmented Slack + Grafana + Jira + GitHub + Notion toolchain.

**Live:**
- Frontend: https://sentinel-hers.vercel.app
- API: https://sentinel-api-clu9.onrender.com
- Demo: `demo@sentinel.io` / `Sentinel2026!`

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Vercel (Next.js 15)                   │
│  Login │ Dashboard │ Incidents │ Monitoring │ Analytics  │
│  War Room: Summary‖RCA ‖ Timeline‖Tasks ‖ Comms ‖ Chat  │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTPS / SSE / WebSocket
┌──────────────────────▼──────────────────────────────────┐
│              Render (FastAPI + Uvicorn)                  │
│  Auth │ Incidents │ Tasks │ SLA │ AI │ Health │ Voice   │
│  Realtime SSE Hub │ WebSocket │ GitHub Webhooks         │
│  Background: Health prober │ AI provider (OpenRouter)   │
└──────────────────────┬──────────────────────────────────┘
                       │ SQLAlchemy
┌──────────────────────▼──────────────────────────────────┐
│      PostgreSQL (Supabase / Render Managed DB)           │
│  incidents, tasks, timeline_events, service_health,     │
│  logs, alerts, deployments, commits, users, teams, roles│
│  channels, messages, anomaly_scores                     │
└─────────────────────────────────────────────────────────┘
```

**Frontend:** Next.js 15 (App Router), Tailwind CSS, shadcn/ui components. Dark theme. Client-side state with deep-link via URL search params.

**Backend:** FastAPI with modular route packages. SQLAlchemy ORM with PostgreSQL. JWT auth with role-based access control (ADMIN, OWNER, RESPONDER, VIEWER). RBAC enforced via `require_permission` dependency on every mutating route.

**Realtime:** SSE stream at `/api/realtime/events?token=<jwt>` with in-memory hub. Events published on incident.create/update/assign/escalate, task.create/update, sla.breach, health.change. WebSocket for bidirectional communication with event-type ACL.

**AI Layer:** Provider abstraction (Claude, Gemini, OpenRouter, NVIDIA). Production uses OpenRouter. AI_PROVIDER=mock hard-fails at boot in production unless ALLOW_MOCK_AI=1. Summary generation, root-cause analysis (5 ranked hypotheses), conversational RAG chat with citations, and structured postmortem with Markdown download.

### Key Design Decisions

1. **Dual-tier auth:** JWT for API authentication (short-lived access + refresh token). RBAC permissions evaluated at the route level via FastAPI dependency injection.

2. **SSE over WebSocket for events:** SSE is simpler for team-scoped event streaming. WebSocket is reserved for bidirectional communication (comms chat, typing indicators).

3. **Seed-driven demo:** The demo user, incidents, tasks, deployments, service health, alerts, log entries, and channel messages are all seeded idempotently on every boot. This ensures judges always land in a non-empty war room.

4. **AI provider abstraction:** All AI features (summary, RCA, chat, postmortem) go through an abstract `AIProvider` interface. Swapping providers requires zero code changes — just set `AI_PROVIDER` env var.

### Security Model

| Layer | Enforcement |
|-------|------------|
| Authentication | JWT with RSA256, refresh token rotation |
| Authorization | 4 roles (ADMIN/*, OWNER/incidents:*, RESPONDER/read+update, VIEWER/*:read) |
| Team isolation | All queries filtered by `team_id` from JWT |
| Rate limiting | Not implemented (deferred) |
| CORS | Explicit allow-list from `CORS_ORIGINS` env var, never `*` |
| Webhook | HMAC signature required in production |
| Secrets | AI keys checked at boot, default JWT secrets refused in prod |
| WS ACL | Only `channel:message`, `typing`, `pong` allowed from clients |

### Functional Requirements Coverage

| # | FR | Status | Notes |
|---|-----|--------|-------|
| 1 | Team auth + RBAC | ✅ | JWT, 4 roles, require_permission on all mutations |
| 2 | Realtime dashboard | ✅ | SSE lifecycle events, auto-open SEV1 war room |
| 3 | Log + alert monitoring | 🔶 | Models + seed data + monitoring page. Log filters TBD |
| 4 | AI summary + RCA | ✅ | Live OpenRouter, 1K+ char summary, 5 RCA hyps, chat, postmortem |
| 5 | GitHub deploys | ✅ | Webhooks + 4 seeded deploys with SHA/author/branch |
| 6 | Service health | ✅ | 5 services, team-scoped, prober wired |
| 7 | Per-incident comms | 🔶 | SSE works, CommsPanel in war room. Multi-channel TBD |
| 8 | Timeline | ✅ | Events on every lifecycle change, GET 200 |
| 9 | Tasks + escalate + SLA | ✅ | CRUD, countdown, breach, escalate API+UI |
| 10 | Analytics | 🔶 | MTTR, severity/status breakdown. Trend charts TBD |

### Brownie Features

| Feature | Status | Notes |
|---------|--------|-------|
| AI Chat | ✅ | RAG over incidents + logs, citations returned |
| Containers | 🟡 | Compose file exists, cloud dashboard shows "unavailable" |
| Postmortem | ✅ | Structured sections + Markdown download |
| Voice-to-ticket | ✅ | Auth from JWT, file upload, mock STT |
| Anomaly detection | ✅ | Autoencoder scores services, analytics risk level |

### Tradeoffs & Known Gaps

1. **No Alembic migrations:** Tables are created via `Base.metadata.create_all()` which is fine for hackathon but not production-grade. A migration tool would be needed for schema evolution.

2. **Single-process hub:** The realtime hub is in-memory. Two uvicorn workers would not share events. A Redis-backed hub is the obvious next step.

3. **Cold start:** Render's free tier spins down after inactivity. First request takes 15-30s. The `WakingOverlay` component shows a visual indicator, but not elegant.

4. **No CI for Playwright:** The Playwright test exists but isn't wired into CI (requires browser binary installation). GitHub Actions can run it with `@playwright/test` and `playwright install chromium`.

5. **Rate limiting:** Auth login has no rate limiting — a brute-force attack is possible. Deferred because the sprint focused on functional breadth.

6. **Test isolation:** Some integration tests share DB state via class-level fixtures (`test_sla.py`). This causes flaky ordering-dependent failures when run as a full suite.

### What I'd Do With More Time

1. Redis-backed SSE hub for multi-worker horizontal scaling
2. Alembic migrations with a `release.sh` script that runs them on deploy
3. Real-time SLA worker (background task that emits breach events proactively instead of on-read)
4. Streaming AI responses for chat (SSE from OpenRouter → SSE to frontend)
5. Full Playwright CI pipeline testing the sacred path against a preview deployment
6. Rate-limited auth endpoint with exponential backoff

### Score Self-Assessment

| Criterion | Weight | Self-score | Rationale |
|-----------|--------|-----------|-----------|
| System Design | 25% | 35% | Modular FastAPI, SSE lifecycle, middleware. No migrations, no Redis |
| Realtime | 20% | 60% | SSE + WS, event ACL, lifecycle events. No multi-worker |
| AI | 20% | 70% | Live OpenRouter, summary+RCA+chat+postmortem. No streaming |
| Security | 15% | 85% | RBAC on all routes, JWT, team isolation. No rate limiting |
| UI/UX | 10% | 35% | Escalate, tasks, AI panels, deep link. Layout needs polish |
| DevOps | 10% | 40% | CI workflow, verify script. No Playwright in CI |
| **Blended** | | **~55-60%** | |

### Verify

```bash
# Live production verification (12 checks)
bash scripts/verify_live.sh

# Backend tests
pytest tests/ -q --tb=short -k "not test_seed and not test_sla"

# Frontend typecheck
cd src/frontend && npx tsc --noEmit

# Frontend build
cd src/frontend && npm run build

# Playwright sacred path
cd src/frontend && npx playwright test --trace on
```
