# SCOREBOARD — SENTINEL HERS
**Date:** 2026-07-26 · re-verified from scratch this session (live browser, direct
curl, dedicated read-only security review, full local test suite) — not carried
forward from prior claims.

**GREEN contract:** must include (1) exact command (2) evidence (3) date. A cell
without evidence stays YELLOW, not GREEN.

| Axis | W | Score | Band | R/Y/G | Evidence | Notes |
|------|---|-------|------|-------|----------|-------|
| Golden path & correctness | 25% | 90 | EXCELLENT | G | Playwright MCP interactive: login (both paths) → dashboard → incidents → war room, all real seeded data, 2026-07-26 | AI summary/RCA blocked by open NVIDIA item (see below); everything else renders |
| Security & tenancy | 15% | 90 | EXCELLENT | G | Dedicated read-only security-review agent, 2026-07-26: no P0/P1. Every data route filters by JWT team_id. bcrypt + JWT rotation + RevokedToken blacklist confirmed | 1 P2 found+fixed (Fernet key regen bug, commit c734eaa). Real minor gaps: no /auth/logout, global (not per-team) webhook secret |
| Architecture & data | 12% | 85 | EXCELLENT | G | FastAPI + SQLAlchemy + Pydantic, Alembic migrations, 18 tables, indexes | pgvector RAG confirmed real (parameterized queries) |
| Reliability & realtime | 12% | 85 | EXCELLENT | G | SSE fixed+verified this session: local live-server repro of 401→200 fix (commit 3e1f1a9); live nav badge shows "connected" | Was a live showstopper before this session's fix — every browser SSE connection 401'd forever |
| AI / integrations | 15% | 40 | THEATER | R | `curl /api/ai/chat` on live API, 2026-07-26: `NVIDIA call failed: 404 page not found` | Code bug fixed (NvidiaProvider missing complete(), commit b7471f3) but NVIDIA's API itself now 404s on the configured model — open item, user resolving the model ID directly |
| UI/UX craft | 10% | 85 | EXCELLENT | G | Live browser walk of dashboard/analytics/monitoring/incidents, 2026-07-26 — no stuck loading states, honest empty states (containers panel) | |
| Proof systems | 6% | 80 | GOOD | G | `bash scripts/verify_live.sh` → PASS, 2026-07-26; full test suite passes 100% per-file | Full combined-suite run has order-dependent flakiness (163-199 passed across reruns) — documented in HANDOFF, not hidden |
| Docs & moat | 5% | 80 | GOOD | G | This file + HANDOFF.md rewritten from live re-verification, not carried-forward claims | |

**Blended (weighted): ~80%** — driven down mainly by the open AI-provider item
(15% weight, currently RED). Every other axis is real and verified GREEN.

## FRs from brief
| FR | Status | Evidence |
|----|--------|----------|
| Team auth + JWT + RBAC | REAL | Security review clean; register() creates isolated team, no cross-tenant bypass |
| Real-time incident dashboard | REAL | Live browser walk, 2026-07-26 |
| AI summaries + RCA | **BLOCKED** | Code fixed, NVIDIA API 404s — see HANDOFF "OPEN" section |
| GitHub/GitLab webhooks | REAL | HMAC-verified (compare_digest), confirmed in security review |
| Service health monitoring | REAL | Live Monitoring page, real alerts + service health |
| Per-incident comms | REAL | Live war room comms panel with seeded message |
| Incident timeline | REAL | Live war room, 4 seeded timeline events |
| Task assignment + SLA | REAL | Live war room, 4 seeded tasks, SLA countdown visible |
| Analytics | REAL | Live page, no stuck loading, real MTTR/severity/anomaly panels |
| Realtime SSE + WS | REAL | Fixed this session (commit 3e1f1a9), live badge shows "connected" |
| Predictive anomaly | REAL | Live analytics panel, per-service IsolationForest scores |
| Container/K8s monitoring | HONEST-EMPTY | "Unavailable — timed out probing" on managed PaaS — correctly reported, not faked |
| Postmortem generation | **BLOCKED** | Same NVIDIA item as AI summaries |
| Voice-to-ticket | PRESENT, NOT DEEP-TESTED | Button renders on Incidents page; mic-input flow not exercised via automated browser (requires device permission grant not practical in this session) |

## P0 / P1 — current
| ID | Issue | Status |
|----|-------|--------|
| — | (none open at P0) | Registration "RBAC bypass" from a prior audit pass was a false positive — reverted the bad fix rather than shipping it (register() always creates a brand-new isolated team; see HANDOFF) |
| P1-open | Live AI provider (NVIDIA) 404s on configured model | Open — user resolving directly |
| P1-minor | No /auth/logout endpoint | Documented, mitigated by short JWT TTL |
| P1-minor | Webhook secret global, not per-team | Documented, acceptable for single-org demo |

## History
| When | Score | Event |
|------|-------|-------|
| 2026-07-26 (this session) | ~80% (AI axis RED pending external fix) | Found+fixed 3 real live bugs (SSE auth header, NVIDIA provider crash, Fernet key), reverted a bad false-positive-driven security "fix", ran dedicated security review (clean), rewrote HANDOFF/SCOREBOARD from live re-verification |
| 2026-07-26 (earlier, same day) | 35% (claimed) | A prior audit pass flagged a false-positive P0 (registration "RBAC bypass") and miscounted tests due to a stale DB journal file corrupting the run — both root-caused and corrected this session |
