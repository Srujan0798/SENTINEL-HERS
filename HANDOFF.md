# HANDOFF — SENTINEL (submission-ready)

**Updated:** 2026-07-26  
**Phase:** FREEZE  
**Live frontend:** https://sentinel-hers.vercel.app  
**Live backend:** https://sentinel-api-clu9.onrender.com  
**Demo credentials:** `demo@sentinel.io` / `Sentinel2026!`

## What works (verified in browser)

- **Login** — renders with "▶ Enter live SEV1 demo" button, auto-fills credentials
- **Dashboard** — 3 incidents (SEV1 investigating, SEV2 triaging, SEV3 resolved), MTTR 47m, SLA breached
- **Incident war room** — AI summary (real OpenRouter LLM), timeline (4 events), tasks (4 with priorities), live chat
- **Root cause analysis** — 5 hypotheses with confidence scores, evidence, suggested actions
- **Analytics** — severity breakdown, top error services, predictive anomaly risk (IsolationForest)
- **Monitoring + Deployments** — pages render with seeded data
- **Settings** — dark mode toggle, team management, theme persistence

## Infrastructure

| Service | URL | Status |
|---------|-----|--------|
| Vercel frontend | https://sentinel-hers.vercel.app | ✅ Serves login, JS hydrates |
| Render API | https://sentinel-api-clu9.onrender.com | ✅ Health 200, CORS OK |
| Render PostgreSQL | managed | ✅ Seeded with 3 incidents |
| Render Redis | managed | ✅ Connected |
| AI | OpenRouter (Claude) | ✅ Real summaries + RCA |
| CI | GitHub Actions `.github/workflows/ci.yml` | ✅ pytest + next lint |

## Key fixes this session

| Fix | File |
|-----|------|
| Removed `output: "standalone"` — was breaking all Vercel routes | `src/frontend/next.config.ts` |
| Tasks endpoint bare list → `{data: [...]}` | `src/backend/tasks/routes.py` |
| AI key persisted to DB — survives restarts | `src/backend/ai/settings.py` + `shared_models.py` + `api/startup.py` |
| Test updated for new response format | `tests/integration/test_sla.py` |
| GitHub Actions CI | `.github/workflows/ci.yml` |
| WRITEUP.md + README updated | Both with live URLs, verified stats |

## Tests

185 passed (baseline, pre-existing errors unchanged by session's work).

## Submission

**GitHub:** https://github.com/Srujan0798/SENTINEL-HERS  
**Frontend:** https://sentinel-hers.vercel.app  
**Write-up:** WRITEUP.md  
**Demo path:** Login → dashboard → SEV1 war room → AI summary → root causes → timeline → tasks → analytics
