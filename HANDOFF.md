# HANDOFF — SENTINEL

> Read this FIRST on any new session (FM-14). Then CLAUDE.md → plan/EXECUTION.md → active spec.
> **Replace, never append** this file (kernel law #8).

- **Active wave:** wave-9 (Submission Hardening) → wave-10 (Brownie & Rubric-Max)
- **Overall status:** Waves 0–8 code is BUILT and on GitHub (`Srujan0798/SENTINEL-HERS`), BUT the
  project is **NOT yet a valid submission** and had a **false-green regression** (see below).

## Ground truth as of 2026-07-23 (orchestrator-verified, not claimed)
- ✅ Substantial real code: backend (all domain modules), Next.js 15 frontend, docker-compose, Prom/Grafana.
- 🟥 **BROKEN:** `src/backend/logs/` package is **missing** — never committed. `ingest`, `ai`, `analytics`
  and 8 test files import it, so the **test suite fails to collect** (8 errors). EXECUTION.md's
  "146 passing" was FALSE on a clean checkout (FM-09). Real test count target: **150**.
- 🟥 **No live deployment** (mandatory submission item). No `render.yaml` / `vercel.json`.
- 🟥 **No `WRITEUP.md`** (mandatory submission item).
- ⚠️ Only 3 commits — judges review commit logs. Wave-9/10 must land as meaningful incremental commits.

## Decisions locked (by human, 2026-07-23)
1. **Deploy:** Render (backend + Postgres + Redis) + Vercel (frontend).
2. **AI:** real Claude/Gemini keys available → wire live, keep mock fallback for tests.
3. **Scope:** GO BIG — mandatory submission bar (wave-9) THEN brownie features (wave-10).

## Next action (critical path)
1. Dispatch **wave-9/01-restore-logs-module** FIRST — it is the blocker; nothing (tests, AI, analytics,
   even backend boot) works without it.
2. Then wave-9/02 (green suite). Then 9/03 (Render) → 9/04 (Vercel) → 9/05 (writeup) ; 9/06 (AI) after 9/01.
3. Then wave-10 fan-out (all 5 brownie tasks) once the suite is green.
4. See `work/DISPATCH.md` for the exact agent assignment + the worker prompt to prepend.

## Dispatch order
`9/01 → 9/02 → {9/03 → 9/04 → 9/05}  ∥  9/06` then `wave-10 (×5 parallel)`.

## Open decisions for the human
- Provide `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` as Render + local env vars (never commit).
- Perform the actual Render + Vercel deploy clicks (r3 blast radius — human action).

## How to resume
1. Read this file. 2. CLAUDE.md (kernel). 3. plan/EXECUTION.md (wave status). 4. work/DISPATCH.md
   (assignments + prompt). 5. orchestrator/agents/REGISTRY.md. 6. Continue from "Next action".
