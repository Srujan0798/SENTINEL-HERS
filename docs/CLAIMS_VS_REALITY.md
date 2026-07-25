# CLAIMS vs REALITY — SENTINEL-HERS
**Date:** 2026-07-25 · **Auditor:** ETERNITY dogfood · **Evidence:** `work/reports/E0-BASELINE.md`

| # | Claim | Source | Probe | Verdict | Evidence | Action |
|---|-------|--------|-------|---------|----------|--------|
| 1 | Submission complete / FINAL | HANDOFF historical | Live audit | **FAKE/OVERCLAIM** | Security+craft gaps remain | Rewrite HANDOFF honest % |
| 2 | Live FE+API demo ready | HANDOFF/PRODUCT | healthz, login, demo-status | **PARTIAL** | health 200, login OK, open SEV1 | Keep; note cold start |
| 3 | AI summaries live | docs | GET summary | **REAL** | 200, MOCK False, prose summary | Keep |
| 4 | Full RBAC | docs/SECURITY | role enforcement history | **PARTIAL** | needs continuous proof | W1 security review |
| 5 | Unauth data impossible | docs/SECURITY | voice/health unauth | **PARTIAL→improved** | 401 on voice+health (2026-07-25) | Was P0; re-verify after deploys |
| 6 | demo credentials for judges | demo-status | GET demo-status | **PARTIAL** | `login_hint` still exposes password | Prod must not leak password |
| 7 | 185 tests = production quality | EXECUTION/HANDOFF | suite vs live | **PARTIAL** | tests exist; not full hostile bar | Don't equate to 100% |
| 8 | Realtime war room live | product | SSE product updates | **PARTIAL** | needs second-tab proof | W4 |
| 9 | Containers on PaaS | monitoring | containers API | **HONEST empty** | PaaS no docker.sock | Label local-only |
| 10 | Analytics always loads | prior browser | hang risk | **PARTIAL** | timeout fix local unpushed? | Verify on Vercel |

**FAKE/OVERCLAIM count:** ≥1 systemic (complete) · **Honesty penalty:** yes if docs still say COMPLETE  
