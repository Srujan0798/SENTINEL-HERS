# HOSTILE GAUNTLET — partial evidence 2026-07-25

## Product
| # | Test | P/F | Evidence |
|---|------|-----|----------|
| P1 | Golden path API | **P** | healthz, login, incidents, AI non-mock (E0-BASELINE) |
| P1b | Browser full path | **?** | Not automated this session |
| P2 | API down ≠ healthy empty | **P** | Dashboard fail-loud error+retry (code) |
| P3 | AI non-mock | **P** | E0-BASELINE MOCK False |
| P4 | Realtime multi-tab | **partial** | Named SSE + FE refresh wired; browser 2-tab not filmed |
| P5 | Mobile | **?** | Not run |
| P6 | Docs match SCOREBOARD | **P** | HANDOFF/SUBMISSION honest ~55-60% |
| P7 | Moat | **P** | docs/MOAT.md |

## TOP-10 security
| # | Probe | P/F | Evidence |
|---|--------|-----|----------|
| S1 | Unauth deny | **P** | voice/health 401 live E0 |
| S2 | Wrong role | **P** | test_rbac_production_routes viewer 403 |
| S3–S4 | Cross-tenant IDOR | **?** | Not dual-tenant scripted |
| S5 | Bad token | **partial** | HTTPBearer 401 expected |
| S6 | Logout/TTL | **partial** | 15m access JWT |
| S7 | Secret leak | **code P / live F** | fixed on main; live still old until Render |
| S8 | Webhook forgery | **P** | tests reject bad sig |
| S9 | SSRF | **?** | N/A light |
| S10 | Misconfig | **partial** | prod JWT required |

**Verdict: FAIL freeze** — S7 live + full browser + IDOR open.  
**Continue after Render deploys main.**
