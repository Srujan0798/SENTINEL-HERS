# HANDOFF — SENTINEL

> Read this FIRST on any new session (FM-14). Then CLAUDE.md → plan/EXECUTION.md → active spec.
> **Replace, never append** this file (kernel law #8).

- **Active wave:** wave-9 (Submission Hardening) → wave-10 after 9.5 + live URLs
- **Overall status:** Wave-9 code path is nearly submission-ready. Suite green. Deploy configs
  present. **Live Render + Vercel clicks + WRITEUP still required** for a valid entry.

## Ground truth as of 2026-07-24 (orchestrator-verified)

| Item | Status | Evidence |
|---|---|---|
| `src/backend/logs/` restored | ✅ | commit `a7d4277` |
| Full pytest suite | ✅ | **150 passed** (post 9.6) · commit `4e84356` + AI wiring |
| Live AI (Claude/Gemini + mock fallback) | ✅ | commit `285bb38` |
| Render blueprint + Dockerfile | ✅ | commit `5e93840` · `render.yaml`, `Dockerfile.api`, `deployment/render/release.sh` |
| CORS from `CORS_ORIGINS` + `requests` + idempotent seed | ✅ | uncommitted → about to merge as 9.3b |
| Vercel frontend config + env wiring | ✅ | uncommitted → about to merge as 9.4 |
| Live deploy URLs | 🟥 | **human action** — Render Blueprint + Vercel project |
| `WRITEUP.md` | 🟥 | wave-9/05 — can draft offline; finalize after live URLs |
| Wave-10 brownie | ⏳ | after suite stays green + optional after writeup |

## Decisions locked (by human)
1. **Deploy:** Render (backend + Postgres + Redis) + Vercel (frontend).
2. **AI:** real Claude/Gemini keys available → wire live, mock fallback for tests.
3. **Scope:** GO BIG — mandatory wave-9 bar, then wave-10 brownie.

## Next action (critical path)
1. Merge local 9.3b + 9.4 (if not yet committed).
2. **Human (r3):** `git push` → Render Blueprint deploy → Vercel deploy (Root = `src/frontend`).
3. Set Render `CORS_ORIGINS` to the Vercel origin; set Vercel `NEXT_PUBLIC_API_BASE_URL` to Render URL.
4. Provide `ANTHROPIC_API_KEY` (and optional `GEMINI_API_KEY`) in Render dashboard only.
5. Dispatch **9.5 WRITEUP** with the two live URLs.
6. Fan out wave-10 (watch AI write-set collisions: 10.1 then 10.4 sequential).

## Open decisions for the human
- Confirm push + deploy clicks.
- Drop API keys into Render (never commit).
- Optional: prefer a custom Vercel domain name.

## How to resume
1. This file → 2. `plan/EXECUTION.md` → 3. `work/DISPATCH.md` → 4. continue from "Next action".
