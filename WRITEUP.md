# SENTINEL — Technical Write-up

**Project:** SENTINEL — AI-Native Engineering Operations Platform (Hard)  
**Author:** Choda Srujan Sai · METIS Development Club / Web & App track  
**Repo:** https://github.com/Srujan0798/SENTINEL-HERS  
**Status of this document:** complete for technical content; **live production URLs** are filled after Render + Vercel deploy (see README).

---

## 1. What & why

Modern engineering teams still respond to production pain with a fragmented toolchain: Slack for paging chatter, Grafana for graphs, Jira for tickets, GitHub for deploys, Notion for postmortems. Context switches burn minutes when every minute of a SEV1 has a dollar cost. SENTINEL is a single operational workspace that unifies:

- live incident triage (severity, assignment, SLA),
- log and alert monitoring,
- AI-generated summaries and root-cause suggestions,
- deployment/commit provenance from GitHub/GitLab,
- team communication channels per incident,
- analytics and predictive anomaly signals,
- optional brownie capabilities (RAG chat, containers, voice-to-ticket, postmortem export).

The product goal is not “another dashboard.” It is a **demo-proof incident path** a judge can walk without leaving the app: login → live SEV1 → AI summary + root cause → assign + escalate with SLA → timeline with provenance → analytics trend.

---

## 2. Architecture & key technical decisions

### Stack (mapped to rubric)

| Choice | Why | Rubric axis |
|--------|-----|-------------|
| **FastAPI + SQLAlchemy 2 + Pydantic 2** | OpenAPI-first contracts, typed request/response, easy test clients | System Design 25% · DevOps 10% |
| **Next.js 15 (App Router) + React 19 + Tailwind/shadcn** | Fast UI iteration, clear route structure for dashboard surfaces | UI/UX 10% |
| **PostgreSQL in prod, SQLite in tests** | Portable column types on a shared Base so CI/local need no external services | DevOps 10% · System Design |
| **SSE primary + WebSockets** | One-way fan-out for incident/status; bidirectional where chat/comms need it | Realtime 20% |
| **Redis** | Pub/sub ready for multi-instance realtime; SLA/timer adjacency | Realtime · System Design |
| **AI provider abstraction** (Claude / Gemini / **mock**) | Live demo with real keys; **deterministic offline tests** without network or secrets | AI 20% · Security 15% |
| **IsolationForest (scikit-learn) + joblib** | Lightweight predictive anomaly without a separate training cluster | AI · System Design |
| **JWT access + refresh, team-scoped RBAC** | Multi-tenant isolation is non-negotiable for logs/chat/webhooks | Security 15% |
| **Prometheus `/metrics` + Grafana assets** | Platform observes itself; judges can see ops maturity | DevOps 10% |
| **Render (API+Postgres+Redis) + Vercel (UI)** | Mandatory live URL path with managed data plane | DevOps 10% |

### Design rules that actually shaped the code

1. **Provider-swappable AI.** `src/backend/ai/provider.py` selects Claude or Gemini from env; missing keys fall back to mock and log a **WARNING** (fail safe + loud — never silent empty AI).
2. **Provenance over polish.** Timeline events and AI outputs are tied to real incident/log IDs so judges can audit “where did this claim come from?”
3. **Graceful external deps.** Docker/K8s clients return `available: false` + reason when no daemon/cluster exists (e.g. on Render free tier) instead of crashing the API process.
4. **Idempotent demo seed.** `scripts/seed_demo.py` (+ release guard) creates the SEV1 once so redeploys do not spam duplicate incidents.
5. **CORS as an explicit allow-list.** Production origins come from `CORS_ORIGINS`; never `*` with credentials.

High-level topology:

```
Browser (Next.js) ──HTTPS/SSE/WS──► FastAPI
                                      ├─ PostgreSQL
                                      ├─ Redis
                                      ├─ AI (Claude/Gemini/mock)
                                      └─ /metrics → Prometheus → Grafana
```

---

## 3. Challenges faced (honest)

### 3.1 False-green regression (the submission killer)

The largest failure was process, not inventiveness. Waves 0–8 looked “shipped” with a claimed **146 tests passing**, but a clean checkout could not even **collect** the suite: `src/backend/logs/` was never committed. An unanchored `.gitignore` rule `logs/` silently ignored `src/backend/logs/`. Downstream modules (`ingest`, `ai`, `analytics`) and eight test files imported it, so the backend could not boot and the entire suite failed at collection.

**Lesson (FM-09):** never mark SHIPPED from a worker’s local green. Re-run acceptance from a clean tree; verify `git ls-files` for every claimed package. Fixed in wave-9 (`a7d4277` restore + gitignore root-anchor `/logs/`).

### 3.2 Shared TestClient poisoning

A stray `import pytz` in `sla/policy.py` (package not installed) broke SLA routes and cascaded into seven anomaly errors via a shared test client. Removing one bad import cleared eight failures. Reminder: dependency honesty beats clever fixture gymnastics.

### 3.3 Deploy reality vs monorepo layout

Render Blueprint + Dockerfile for the API was straightforward; the frontend lives under `src/frontend/`, so Vercel **Root Directory** must be set explicitly. CORS must be updated **after** the Vercel hostname is known — order matters.

### 3.4 Dual-tier orchestration under rate limits

Work was split: orchestrator owns task files, acceptance, and merges; external agents own write-sets. Parallel agents with disjoint write-sets worked (Render vs AI wiring). Rate limits mid-task taught us to keep every task file fully self-contained so a new agent can resume without chat history.

### 3.5 Security tradeoffs

Webhook secrets and JWT lengths were hardened for tenant scope; some demo paths intentionally keep the seeded password documented so judges can enter the product. Production secrets stay dashboard-only (`sync: false` on Render).

---

## 4. What I would do with more time

1. **CI on every PR** — clean-container `pytest -q` + frontend `npm run build` so missing packages never land again.
2. **True multi-instance realtime** — Redis-backed fan-out verified under load, not just single-process SSE.
3. **Richer RAG** — embedding index over logs with freshness windows, not only top-k SQL retrieval.
4. **PDF postmortem export** — Markdown is shipped; PDF needs a headless renderer in the deploy image.
5. **SLO burn-rate alerts** wired from Prometheus into the same incident pipeline that humans already use.
6. **E2E Playwright** of the sacred demo path against the live Render+Vercel pair.
7. **Upgrade Next.js** past the advisory version currently pinned for the build.

---

## 5. Verification snapshot (no invented metrics)

| Check | Result | Source |
|-------|--------|--------|
| Full pytest suite | **150 passed**, 0 failed, 0 errors | Independent run after wave-9/03b+04 (2026-07-24) |
| Frontend production build | `✓ Compiled successfully` with `NEXT_PUBLIC_API_BASE_URL=https://example.test` | wave-9/04 acceptance |
| Logs package tracked in git | Restored + committed | `a7d4277` |
| Live AI wiring | Claude/Gemini + mock fallback; mock tests green | `285bb38` |
| Render blueprint | `render.yaml` + `Dockerfile.api` + release migrate/seed | `5e93840` |
| Vercel config | `src/frontend/vercel.json` + public env docs | `acccc70` |

Local demo credentials (seeded, intentional): `demo@sentinel.io` / `Sentinel2026!`

---

## 6. Closing

SENTINEL is built as a production-leaning hackathon system: real modules, real tests, deploy blueprints, and an honest accounting of the false-green trap that almost erased the submission. The remaining human gate is the live Render + Vercel pair and embedding those URLs in README for judges. Everything else is designed so an external agent fleet can harden brownie features without rewriting the core.
