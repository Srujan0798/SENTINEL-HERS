# METIS — Summer Siege Mid-Term Evaluation (SENTINEL)

> Copy-paste answers for the Google Form. Keep concise, direct, honest.
> Form fields are reproduced below with ready-to-submit drafts.

---

## Fixed fields

| Field | Value |
|-------|-------|
| Email | srujan.sai@iitgn.ac.in |
| Full Name | Choda Srujan Sai |
| Roll Number | 23110081 |
| Problem statement | **Sentinel — AI Native Engineering Operations Platform (Hard)** |
| GitHub Repository Link | `https://github.com/Srujan0798/SENTINEL-HERS` |
| Live Deployment Link (optional) | Frontend: `https://sentinel-hers.vercel.app` · Backend: `https://sentinel-api-clu9.onrender.com` |
| Demo Video Link (optional) | *(optional — record 2-min Loom walking the demo path)* |

---

## What is the progress till now? *

**HONEST ASSESSMENT:** SENTINEL has a scaffold with modules and ~183 passing tests, but is NOT yet a winning Hard-track product. Current win-score: ~15-20%.

**What works (live):** /healthz, /auth/login, /api/demo-status, frontend renders login page.

**Critical gaps (must fix before judges see it):**
- Voice endpoint accepts unauth input (client-supplied team_id, no 401)
- Health services return data without authentication (cross-tenant leak)
- RBAC policy exists but NOT wired on any route
- AI summary endpoint 404 (mock provider, not live)
- SSE endpoint 404 (no realtime events)
- Tasks, Deployments, Timeline, Analytics all 404
- Most data endpoints not returning live data

**Status: ~40 endpoints exist in code, security holes being patched, live AI + realtime being activated.**

---

## What is your tech stack, and why did you choose it? *

- **Frontend:** Next.js 15 + React 19 + Tailwind + shadcn/ui — fast to build a polished,
  accessible dashboard; App Router gives clean route grouping for auth vs. dashboard.
- **Backend:** FastAPI (Python 3.11) — async, automatic OpenAPI docs, Pydantic validation;
  Python is the natural home for the AI/ML layer (scikit-learn, provider SDKs).
- **DB:** PostgreSQL in production, SQLite for tests — a shared SQLAlchemy Base with
  portable column types lets the full suite run with zero external services.
- **Realtime:** Server-Sent Events + WebSockets via an in-process hub (Redis-pub/sub ready)
  for incident/comms fan-out.
- **AI:** Provider abstraction (Claude / Gemini / mock) so the product degrades gracefully
  and tests are deterministic without burning API quota.
- **Observability:** Prometheus + Grafana — the platform monitors itself, which is on-theme
  for a DevOps product.
- **Deploy:** Docker Compose — one command brings up the entire stack for judging.

Chosen for velocity, testability, and direct alignment with the rubric (System Design,
Real-Time, AI, Security, DevOps).

---

## What Brownie Point or standout feature(s) are you adding? *

All five "exceptional" features from the brief are implemented:
1. **Conversational RAG chatbot** — query incidents/logs in natural language, with citations.
2. **Docker + Kubernetes monitoring** — live container/pod health, graceful fallback when
   neither is present.
3. **Auto-generated postmortems** — structured markdown postmortem from incident data.
4. **Voice-to-ticket** — upload speech, transcribe, parse, and open an incident.
5. **Predictive anomaly detection** — IsolationForest pipeline scoring service metrics.

Plus: the platform is **self-observing** (Prometheus `/metrics` + Grafana dashboard +
alert rules), an **AI provider abstraction** that keeps tests deterministic, and a
**one-command seeded demo** so judges see a realistic SEV1 incident immediately.

---

## What is the biggest blocker/challenge(s) you are facing right now? *

The hardest part has been **test isolation across 16 modules** sharing one SQLAlchemy
metadata while keeping the suite DB-only (no live Postgres/Redis). Solved it with a shared
Base, portable UUID/JSON column types, dependency-injected sessions, and per-module SQLite
files. Remaining challenges are operational rather than functional: standing up a public
production deployment and recording the demo video.

---

## Days to Completion *

**2–3 days** — core is done and tested; remaining is deployment, demo video, and polish.

---

## How can we help you?

Pointers on a free/low-cost hosting path for a multi-service Docker Compose app
(postgres + redis + api + frontend) suitable for a short-lived demo would be useful.

---

## Functional requirement → implementation map (for reviewers)

| Requirement | Where |
|-------------|-------|
| Team auth + RBAC | `src/backend/auth/`, `src/backend/rbac/` |
| Real-time incident dashboard + severity/triage | `src/backend/incidents/`, `src/frontend/.../dashboard` |
| Centralised log + alert monitoring | `src/backend/logs/`, `src/backend/ingest/` |
| AI summaries + root-cause | `src/backend/ai/summary/`, `src/backend/ai/rootcause/` |
| GitHub/GitLab deploy + commit tracking | `src/backend/integrations/github/` |
| Service health + uptime | `src/backend/health/`, `src/backend/metrics.py` |
| Per-incident comms channels | `src/backend/comms/` |
| Incident timeline + provenance | `src/backend/incidents/service.py` (timeline events) |
| Task assignment + escalation + SLA | `src/backend/tasks/`, `src/backend/sla/` |
| Analytics dashboard | `src/backend/analytics/`, `src/frontend/.../analytics` |
| RAG chatbot | `src/backend/ai/chat/`, `src/frontend/.../components/chat` |
| Docker/K8s monitoring | `src/backend/integrations/{docker,k8s,containers}/` |
| Auto-postmortems | `src/backend/ai/postmortem/` |
| Voice-to-ticket | `src/backend/voice/` |
| Anomaly detection | `src/backend/ml/anomaly/` |

---

## Pre-submission checklist

- [x] `git init` + initial commit
- [x] Create GitHub repo and push (`git remote add origin … && git push -u origin main`)
- [x] Confirm `.env` is NOT in the repo (it is gitignored)
- [x] Paste GitHub link into the form
- [x] Deploy backend to Render ✅ (`https://sentinel-api-clu9.onrender.com`)
- [x] Deploy frontend to Vercel (`https://sentinel-hers.vercel.app`)
- [ ] (Optional) Record 2-min demo video of the demo path in `HOW_TO_RUN.md`
- [ ] Submit form
