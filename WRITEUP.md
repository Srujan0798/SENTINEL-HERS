# SENTINEL — Technical Write-up

**Project:** SENTINEL — AI-Native Engineering Operations Platform (Hard)  
**Author:** Choda Srujan Sai · METIS Development Club / Web & App track  
**Repo:** https://github.com/Srujan0798/SENTINEL-HERS  
**Live frontend:** https://sentinel-hers.vercel.app  
**Live API:** https://sentinel-api-clu9.onrender.com  
**Demo credentials:** `demo@sentinel.io` / `Sentinel2026!`

---

## 1. What & why

Modern engineering teams respond to production pain with a fragmented toolchain: Slack for paging, Grafana for graphs, Jira for tickets, GitHub for deploys, Notion for postmortems. Context switches burn minutes when every minute of a SEV1 has a dollar cost.

SENTINEL is a single operational workspace that unifies:
- live incident triage (severity, SLA, assignment),
- log and alert monitoring,
- AI-generated summaries and root-cause hypotheses,
- deployment/commit provenance,
- team chat per incident,
- analytics and predictive anomaly signals,
- optional brownie capabilities (RAG, voice-to-ticket, postmortem export).

The sacred demo path a judge can walk without leaving the app:  
**Login → live SEV1 → AI summary + root cause → assign + escalate with SLA timer → timeline with provenance → analytics trend.**

---

## 2. Architecture & key technical decisions

### Stack

| Choice | Why | Rubric axis |
|--------|-----|-------------|
| **FastAPI + SQLAlchemy 2 + Pydantic 2** | OpenAPI-first contracts, typed request/response, fast test clients | System Design 25% · DevOps 10% |
| **Next.js 15 (App Router) + React 19 + Tailwind/shadcn** | Fast UI iteration, clear route structure for dashboard surfaces | UI/UX 10% |
| **PostgreSQL in prod, SQLite in tests** | Portable column types on shared Base; CI/local need no external services | DevOps 10% · System Design |
| **SSE primary + WebSockets** | One-way fan-out for incident/status; bidirectional for chat | Realtime 20% |
| **Redis** | Pub/sub for multi-instance realtime; SLA adjacency | Realtime · System Design |
| **AI provider abstraction** (OpenRouter → Claude/Gemini/mock) | Live demo with real keys; deterministic offline tests without network or secrets | AI 20% · Security 15% |
| **IsolationForest (scikit-learn) + joblib** | Lightweight predictive anomaly without a separate training cluster | AI · System Design |
| **JWT access + refresh, RBAC** | Multi-tenant isolation for logs/chat/webhooks | Security 15% |
| **Prometheus /metrics + Grafana** | Platform observes itself | DevOps 10% |
| **Render (API+Postgres+Redis) + Vercel (UI)** | Mandatory live URL path with managed data plane | DevOps 10% |

### Design rules

1. **Provider-swappable AI** — `src/backend/ai/provider.py` selects OpenRouter/Claude/Gemini from env; missing keys fall back to mock and log WARNING (fail loud — never silent empty AI).
2. **Provenance over polish** — Timeline events and AI outputs tied to real incident IDs for auditability.
3. **Graceful external deps** — Docker/K8s clients return `available: false` + reason instead of crashing.
4. **Idempotent demo seed** — `/api/seed` creates the SEV1 once; redeploys don't duplicate.
5. **CORS as explicit allow-list** — Production origins from env var; never `*` with credentials.

```
Browser (Next.js) ──HTTPS/SSE/WS──► FastAPI
                                      ├─ PostgreSQL
                                      ├─ Redis
                                      ├─ AI (OpenRouter/Claude/Gemini/mock)
                                      └─ /metrics → Prometheus → Grafana
```

---

## 3. Challenges faced

### 3.1 The false-green regression trap (FM-09)

Waves 0–8 claimed **146 tests passing**, but a clean checkout could not even collect the suite: `src/backend/logs/` was never committed. An unanchored `.gitignore` rule `logs/` silently swallowed the package. Downstream modules and eight test files imported it, so the entire suite failed at collection.

**Fix:** never mark SHIPPED from a worker's local green. Re-run acceptance from a clean tree; verify `git ls-files` for every claimed package.

### 3.2 `output: "standalone"` broke all Vercel routes

The Next.js config had `output: "standalone"` which is incompatible with Vercel's serverless runtime. Every route returned a 404 page. Removing this single line fixed all frontend routing.

### 3.3 Tasks endpoint returned bare list

The tasks API returned `[...]` instead of `{data: [...]}`, breaking the frontend data contract. Fixed the response format and updated the test.

### 3.4 Shared TestClient cascading failures

A stray `import pytz` in `sla/policy.py` (package not installed) broke SLA routes and cascaded into seven anomaly errors via a shared test client. One import fix cleared eight failures.

### 3.5 Vercel edge cache stale after deploy

After deploying, the production URL served a stale prerendered shell. Vercel has no public edge-cache purge API, but the new build's assets are correct — the page renders fully after JS hydration in a browser.

---

## 4. What I would do with more time

1. **CI on every PR** — clean-container `pytest -q` + `npm run build` so missing packages never land again.
2. **Multi-instance realtime** — Redis-backed fan-out verified under load, not single-process SSE.
3. **Richer RAG** — embedding index over logs with freshness windows, not just top-k SQL retrieval.
4. **PDF postmortem export** — headless renderer in the deploy image.
5. **SLO burn-rate alerts** wired from Prometheus into the incident pipeline.
6. **E2E Playwright test** of the sacred demo path against live Render+Vercel.
7. **Persist AI key on Render** via dashboard env vars for survival across restarts.

---

## 5. Verification snapshot (verified live on 2026-07-25)

| Check | Result | How verified |
|-------|--------|-------------|
| Full pytest suite | **185 passed**, 0 failed, 0 errors | `pytest -q -W ignore::DeprecationWarning —tb=short` |
| Frontend build | `✓ Compiled successfully` | Vercel deploy log `dpl_FyTaKcFQFYnTao9ed9gans8qmos1` |
| Login page | Renders with demo credentials + "▶ Enter live SEV1 demo" button | Playwright browser snapshot |
| Dashboard | Shows 3 incidents, 1 SEV1 active, MTTR 47m | Playwright browser snapshot |
| Incident war room | AI summary, timeline (4 events), tasks (4 items), chat, SLA timer | Playwright browser snapshot |
| Root Cause Analysis | Generates real LLM hypotheses | Clicked via browser |
| Analytics | Total=3, MTTR=47m, severity breakdown, error services, anomaly risk | Playwright browser snapshot |
| Live AI wiring | OpenRouter provider returns real summary + hypotheses | Backend logs + browser |
| CORS | Allows Vercel origin | Browser network tab — no CORS errors |
| Backend health | `healthz` 200 | `curl https://sentinel-api-clu9.onrender.com/healthz` |
| No console errors | 0 errors, 0 warnings | Playwright console output |
| Tests collect clean | All 185 tests discoverable | `pytest --collect-only` |

---

## 6. How to demo (for judges)

1. Open https://sentinel-hers.vercel.app/login
2. Click **"▶ Enter live SEV1 demo"** (auto-fills credentials)
3. **Dashboard** — see 3 incidents, MTTR 47m, SLA breached
4. Click the SEV1 incident ("Payment service cascade failure")
5. **War room** — read AI-generated summary, click "Root Cause Analysis"
6. See **Timeline** (4 events), **Tasks** (4 items with checkboxes)
7. Use **Incident Comms** chat panel
8. Navigate to **Analytics** — severity breakdown, error services, anomaly risk
9. Navigate to **Monitoring** and **Deployments** pages

All data is pre-seeded: 3 incidents (SEV1 investigating, SEV2 triaging, SEV3 resolved), 4 deployments, 5 service health records.

---

## 7. Closing

SENTINEL ships as a production-leaning system: real modules, real tests (185 passing), real deploy blueprints on Render + Vercel, and real AI integration via OpenRouter. The end-to-end demo path is verified working in a live browser. The false-green trap that almost erased the submission is documented honestly. Everything is designed so the platform can be hardened further without rewriting the core.
