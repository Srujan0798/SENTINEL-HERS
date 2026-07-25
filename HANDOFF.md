# HANDOFF — SENTINEL HERS (HONEST)

> Win-score ≈ **45-55%** (from ~15%). All Phase 0-3 complete, Phase 4 in progress.

## Live
| Item | Value |
|------|--------|
| Frontend | https://sentinel-hers.vercel.app |
| Backend | https://sentinel-api-clu9.onrender.com |
| Demo | `demo@sentinel.io` / `Sentinel2026!` |
| GitHub | https://github.com/Srujan0798/SENTINEL-HERS |

## What Works (verified live)
- `/healthz` → 200
- `/auth/login` → JWT with role
- `/api/demo-status` → ready, 1 open SEV1, **no password leak**
- **AI Summary** → 1,328 chars real text (OpenRouter, not mock)
- **AI RCA** → 5 hypotheses via POST `/api/ai/incidents/{id}/root-causes`
- **Incidents** → 3 incidents, CRUD + timeline + status transitions
- **Tasks** → CRUD, toggle status
- **SLA** → countdown + breach detection
- **Health** → 5 services, team-scoped
- **Deployments** → 4 deploys, webhook sig required in prod
- **SSE** → `event: connected` at `/api/realtime/events?token=<jwt>`
- **Voice → tickets** → file upload auth from JWT
- **Chat AI** → POST `/api/ai/chat` with citations
- **Postmortem** → GET `/api/ai/postmortem/{id}` (json or markdown download)
- **Escalate** → POST `/api/incidents/{id}/escalate` with reason
- **Timeline** → events on create, status, assign, escalate
- **Auth** → JWT with RBAC, require_permission on all mutating routes

## Security (P0 fixes deployed)
- [x] Voice auth from JWT (no client team_id)
- [x] Health auth + team filter
- [x] RBAC wired on mutations (ADMIN/OWNER/RESPONDER/VIEWER)
- [x] Webhook sig required in production
- [x] demo-status hides password in production
- [x] Task incident ownership check
- [x] WS event ACL (only channel:message/typing/pong)
- [x] JWT secrets refuse defaults in production
- [x] AI provider boot check (fails if mock in prod without ALLOW_MOCK_AI=1)
- [x] Tests: test_rbac (24) + test_security_tenancy (7) + test_incidents (14) + test_voice (13)

## What is BROKEN / Missing
1. Frontend war room: No deep-link `/incidents/[id]` (state-based selection)
2. Monitoring: No prober running on Render (wired but needs ENABLE_HEALTH_PROBER=1)
3. Analytics APIs return mostly empty data (seed only has 3 incidents)
4. No CI/CD pipeline (GitHub Actions, Playwright)
5. No Playwright browser tests for sacred path
6. Cold start on Render (no keep-alive)
7. GitLab integration not tested
8. Log level filters not implemented
9. Deploy stability metric not in analytics

## Frontend Features (added this session)
- [x] Escalate button with reason dialog
- [x] Create Task dialog
- [x] Separate AI Summary and RCA panels (RCA no longer overwrites summary)
- [x] verify_live.sh script (12 checks, 9/12 pass against current live)

## Next: Phase 4+ remaining work
- Phase 4E: Analytics consistency (seed more data, fix empty panels)
- Phase 5: Brownie excellence (chat citations, containers, postmortem, voice, anomaly)
- Phase 6: System design (indexes, architecture diagram, metrics)
- Phase 7: UI domination (deep link, war room layout, dark theme consistency)
- Phase 8: CI (GitHub Actions, Playwright, verify_live.sh in CI)
- Phase 9: Freeze (security review, SCOREBOARD re-score)

## Plan Reference
- Full plan: `work/ETERNAL_FINAL_PLAN.md`
- Scoreboard: `docs/SCOREBOARD.md`
- verify script: `scripts/verify_live.sh`
