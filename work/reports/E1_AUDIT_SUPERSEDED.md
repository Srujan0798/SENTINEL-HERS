> **SUPERSEDED 2026-07-26 (later same day):** the "163 passed/34 errors" reading below was
> corrupted by a stale `sentinel_test.db-journal` file (fixed, commit 79b785b). The
> P0-1 "registration RBAC bypass" finding was a false positive: `register()` always
> creates a brand-new, uniquely-slugged team, so a self-registered admin is admin only
> of their own isolated workspace — standard self-serve SaaS behavior, not a
> cross-tenant bypass. See `HANDOFF.md` and `docs/SCOREBOARD.md` for the corrected,
> re-verified state. Kept here for traceability only — do not treat as current truth.

# Phase 1 Audit: SENTINEL-HERS Brutal 360° (SUPERSEDED)
**Date:** 2026-07-26  
**Auditor:** ETERNITY v3.2 Hostile Validator  
**Project root:** /Users/srujansai/Desktop/SENTINEL-HERS  
**Live FE:** https://sentinel-hers.vercel.app  
**Live API:** https://sentinel-api-clu9.onrender.com  

## Honest Score

| Metric | Claimed | Actual | Verdict |
|--------|---------|--------|---------|
| Test pass rate | 177 passed, 0 failed | 163 passed, 3 failed, 34 errors | **FAKE** |
| verify_live.sh | 13/13 PASS | 13/13 PASS | **REAL** |
| SCOREBOARD | ~98-100% all GREEN | Security RED (P0 open) → cap 40% | **FAKE** |
| CLAIMS_VS_REALITY | 0 FAKE | P0 RBAC bypass undisclosed | **FAKE** |
| HANDOFF | 199 passed | 163 passed + 3 failed + 34 errors | **FAKE** |
| WRITEUP | 182+ passed | 163 passed + 3 failed + 34 errors | **FAKE** |
| README badge | 199 passing | Wrong count | **FAKE** |
| Golden path (Playwright) | Walkthrough works | Broken (async test.describe, no browsers) | **FAKE** |
| AI live | Real OpenRouter | Real OpenRouter works | **REAL** |
| API health | 200 | 200 | **REAL** |
| Login works | Yes | Yes | **REAL** |
| Unauth deny | 401/403 | 401/404 confirmed on live | **REAL** |
| RBAC (role enforcement) | Working | P0 bypass via registration | **FAKE** |
| Demo credentials | demo@sentinel.io / Sentinel2026! | Works, but user is admin by default | **PARTIAL** |

## Verification

All verdicts derived from direct execution of `preflight.sh`, `check_entailment.sh`, and `pytest -q --tb=no` against SENTINEL-HERS at commit `e5befc0a` on 2026-07-26. See HANDOFF.md for current verified state; this file is SUPERSEDED and retained for traceability only.

**35% (BAND: THEATER)** — capped at 40% by ETERNITY L11 (Security P0 open)

### Axis breakdown
| Axis | Claimed | Actual | Cap |
|------|---------|--------|-----|
| Golden path & correctness | ~95% | ~85% | — |
| Security & tenancy | ~100% | ~20% (P0 bypass) | ≤40% |
| Architecture & data | ~90% | ~80% | — |
| Reliability / realtime | ~90% | ~85% | — |
| AI / integrations | ~100% | ~95% | — |
| UI/UX craft | ~95% | ~80% | — |
| Proof systems | ~90% | ~60% (verify_live pass + test count fraud) | — |
| Docs & moat | ~90% | ~70% (test counts wrong, claims inflated) | — |

Blended with security cap: **~35%**

## P0 Findings

### P0-1: Registration RBAC Bypass (SEVERITY: P0 - DQ)
- **File:** `src/backend/auth/service.py:140-147`, `214`
- **Root cause:** `create_user()` hardcodes `admin_role` lookup. All new users get admin role regardless of intent.
- **Impact:** ANY user can register and gain admin privileges → full RBAC bypass. Can access AI settings, invite users, manage teams.
- **Evidence:** Registered `sec@test.com` → JWT contains `"role": "admin"` → `POST /api/ai/settings` returns 200 (admin endpoint)
- **Probe:** `POST /auth/register` with any email → `POST /api/ai/settings` returns 200 instead of 403
- **Fix required:** Remove hardcoded admin default; add role selection on registration or default to lowest role.

### P0-2: Test Count Fraud (severity: P1 - claims integrity)
- **Claimed:** "199 passed, 0 failed" (README), "177 passed, 21 pre-existing errors"
- **Actual:** 163 passed, 3 failed, 34 errors in full suite
- **Error type:** All 34 errors are `sqlite3.OperationalError: table teams already exists` — SQLite table creation race condition in parallel test execution
- **Failure type:** 3 RBAC production route tests fail in full suite but pass individually (test isolation/DB state issue)
- **Probe:** `AI_PROVIDER=mock python -m pytest -q --tb=no` → "3 failed, 163 passed, 34 errors"

## P1 Findings

### P1-1: No Logout Endpoint (S6)
- No `/auth/logout` endpoint exists. Tokens remain valid until natural expiry.
- No token revocation mechanism beyond the RevokedToken blacklist (which has no cleanup cron).

### P1-2: Playwright Broken
- `test.describe()` is async in sacred-path.spec.ts → Playwright error
- Chromium was not pre-installed → requires `npx playwright install`
- Golden path cannot be verified by Playwright

### P1-3: OpenAPI Docs Exposed (S10)
- 47 endpoints exposed at `/docs/openapi.json` and `/docs`
- Server header reveals `uvicorn` + cloudflare
- Shared webhook secret (per source comment, not per-team)

### P1-4: RBAC Test Isolation
- 3 RBAC tests fail in full suite but pass individually due to shared SQLite DB state
- Test suite cannot run in parallel without DB corruption

## REAL ✅
- verify_live.sh: 13/13 PASS
- API healthz: 200
- Demo-status: no password leak, returns live data
- Login: JWT works
- Bad token rejection: 401
- AI chat SSRF blocked: 422
- Unauth deny: 401/404 on production routes
- FE login page serves (Next.js SPA)
- AI is real OpenRouter (not mock on live)
- Demo credentials work

## PARTIAL ⚠️
- Demo user (demo@sentinel.io) is admin — all accounts are admin, which is expected for a demo but the registration bypass makes it worse
- Cross-tenant isolation: 404 for non-existent incidents (proper but can't test with real cross-tenant data)
- Webhook security: shared secret, not per-team

## FAKE ❌
- Test count claims (README, HANDOFF, WRITEUP, SCOREBOARD)
- All axes GREEN on SCOREBOARD (Security axis is RED)
- CLAIMS_VS_REALITY 0 FAKE (P0 not disclosed)
- Playwright golden path working
- "100% push" / "all features complete" claims
