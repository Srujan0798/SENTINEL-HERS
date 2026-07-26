# CLAIMS vs REALITY — SENTINEL-HERS
**Date:** 2026-07-26 · **Auditor:** ETERNITY · **Phase:** Submit-ready

| # | Claim | Source | Probe | Verdict | Evidence | Action |
|---|-------|--------|-------|---------|----------|--------|
| 1 | Submission complete — all 10 FRs done | SCOREBOARD + WRITEUP | verify_live + pytest + browser | **REAL** | 177 passed, 13/13 live checks, Playwright sacred path, all FRs ✅ | Keep |
| 2 | Live FE+API demo | HANDOFF | healthz, login, dashboard | **REAL** | health 200, login OK, SEV1 war room renders | Keep; cold start noted |
| 3 | AI summaries live | docs | POST /api/ai/summary | **REAL** | 200, MOCK=false, prose summary + RCA | Keep |
| 4 | Full RBAC | docs | role enforcement probes | **REAL** | 4 roles, require_permission on all mutations, team isolation via JWT | Keep |
| 5 | Unauth impossible | docs | voice/health/unauth probes | **REAL** | 401 on unauth access, 422 on malformed | Keep |
| 6 | Demo credentials for judges | demo-status | GET demo-status | **REAL** | `login_hint` returns hint only (no password leak) | Keep |
| 7 | Realtime live | product | second-tab SSE test | **REAL** | Redis pub/sub + in-memory hub, second-tab updates verified | Keep |
| 8 | Rate limiting applied | api/main.py | test rate-limited endpoint | **REAL** | slowapi on auth register (60/min) + login (5/min) | Keep |
| 9 | Webhook security | integration routes | HMAC + token test | **REAL** | GitHub HMAC-SHA256 + GitLab X-Gitlab-Token, 401 in prod | Keep |
| 10 | pgvector RAG | ai/embeddings.py | vector search query | **REAL** | 768-dim NVIDIA embeddings, HNSW index, cosine similarity, keyword fallback | Keep |

**FAKE/OVERCLAIM count:** 0 · **Honesty penalty:** none

All claims verified fresh 2026-07-26. Evidence paths in SCOREBOARD.md.
