# SENTINEL — System Architecture

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         JUDGE / USER BROWSER                         │
│                    (Incognito → sentinel-hers.vercel.app)            │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ HTTPS + SSE + WebSocket
                                 │
┌────────────────────────────────▼────────────────────────────────────┐
│                      VERCEL (Next.js 15 Frontend)                    │
│                                                                      │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌──────────┐           │
│  │  Login   │  │ Dashboard │  │ Incidents│  │Monitoring│           │
│  │ Register │  │  KPIs     │  │ War Room │  │  Health  │           │
│  └──────────┘  └───────────┘  └──────────┘  └──────────┘           │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌──────────┐           │
│  │ Analytics│  │Deployments│  │ Settings │  │   Chat   │           │
│  │ MTTR+RCA │  │  SHA+Git  │  │  Roles   │  │   RAG    │           │
│  └──────────┘  └───────────┘  └──────────┘  └──────────┘           │
│                                                                      │
│  Components: WakingOverlay (cold-start), SSE StatusBar, ChatPanel    │
│  Deep link: /incidents?id=<uuid>                                     │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ REST API + SSE
                                 │
┌────────────────────────────────▼────────────────────────────────────┐
│                   RENDER (FastAPI + Uvicorn)                         │
│                   ENV=production · Rate-limited                      │
│                                                                      │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ ┌─────────┐    │
│  │  Auth   │ │Incidents │ │  Tasks   │ │  SLA    │ │   AI    │    │
│  │JWT+RBAC │ │Escalate  │ │ CRUD     │ │Countdown│ │Summary  │    │
│  │Rate-lim │ │Timeline  │ │ Create   │ │ Breach  │ │RCA+Chat │    │
│  └─────────┘ └──────────┘ └──────────┘ └─────────┘ └─────────┘    │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌─────────┐ ┌─────────┐    │
│  │ Health  │ │  Voice   │ │  Comms   │ │GitHub   │ │Analytics│    │
│  │ Prober  │ │  STT     │ │ SSE Chan │ │Webhooks │ │MTTR+Trend│   │
│  └─────────┘ └──────────┘ └──────────┘ └─────────┘ └─────────┘    │
│                                                                      │
│  Middleware: CORS allow-list · Rate limiting (slowapi) · Prometheus  │
│  Realtime Hub: SSE /api/realtime/events · WS /api/ws                │
│  Boot checks: AI provider ≠ mock · JWT secrets set · ENV=production  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ SQLAlchemy ORM
                                 │
┌────────────────────────────────▼────────────────────────────────────┐
│              POSTGRESQL (Render Managed · 16 tables)                │
│                                                                      │
│  users · teams · roles · incidents · timeline_events · tasks        │
│  log_entries · alerts · service_health · deployments · commits      │
│  channels · messages · channel_members · anomaly_scores             │
│                                                                      │
│  18 indexes: team_id, status, severity, detected_at, created_at     │
│  Composite: (team_id, status, severity) · (team_id, status, sla)    │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                     EXTERNAL AI PROVIDER                             │
│  OpenRouter (production) → Claude / Gemini / NVIDIA models           │
│  Provider abstraction: AIProvider interface (swap via env var)       │
│  Mock provider: TESTS ONLY · boot fails in prod without ALLOW_MOCK  │
└─────────────────────────────────────────────────────────────────────┘
```

## Request Flow (Sacred Demo Path)

```
1. Browser → Vercel → /login
2. POST /auth/login → JWT (15min access + 30d refresh)
3. GET /api/incidents → SEV1 auto-selected
4. GET /api/ai/incidents/{id}/summary → OpenRouter → 1.3K char summary
5. POST /api/ai/incidents/{id}/root-causes → 5 ranked hypotheses
6. GET /api/realtime/events?token=JWT → SSE "event: connected"
7. POST /api/incidents/{id}/assign → timeline event + SSE publish
8. POST /api/incidents/{id}/escalate → timeline event + SSE publish
9. POST /api/incidents/{id}/tasks → task created + SSE publish
10. GET /api/analytics/incidents/summary → MTTR, severity breakdown
```

## Security Layers

```
┌─────────────────────────────────────────────┐
│ Layer 1: CORS allow-list (no wildcard)      │
├─────────────────────────────────────────────┤
│ Layer 2: Rate limiting (login 10/min)       │
├─────────────────────────────────────────────┤
│ Layer 3: JWT auth (Bearer token, 15min TTL) │
├─────────────────────────────────────────────┤
│ Layer 4: RBAC (ADMIN/OWNER/RESPONDER/VIEWER)│
├─────────────────────────────────────────────┤
│ Layer 5: Team isolation (team_id from JWT)  │
├─────────────────────────────────────────────┤
│ Layer 6: Webhook HMAC sig (production only) │
├─────────────────────────────────────────────┤
│ Layer 7: WS event ACL (3 types only)        │
├─────────────────────────────────────────────┤
│ Layer 8: Boot checks (JWT/AI/prod secrets)  │
└─────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, React 19, Tailwind CSS, shadcn/ui |
| Backend | FastAPI, Python 3.11, Uvicorn |
| Database | PostgreSQL 16 (Render Managed) |
| Realtime | SSE + WebSocket (in-memory hub) |
| AI | OpenRouter (Claude/Gemini/NVIDIA) |
| Auth | JWT (HS256), RBAC, bcrypt |
| Metrics | Prometheus (request latency, incident gauges) |
| Rate Limiting | slowapi (IP-based, login 10/min) |
| CI | GitHub Actions (pytest + tsc + build) |
| Deploy | Render (backend), Vercel (frontend) |