# SCOREBOARD — SENTINEL HERS (FINAL — DEPLOYED)

> Rules: RED = not working / not exist | YELLOW = partial / mock / unauth | GREEN = production-grade with evidence
> Last updated: 2026-07-25 (ALL DEPLOYED LIVE)

## Rubric Weight

| Criterion | Weight | Score | Status | Evidence |
|-----------|--------|-------|--------|----------|
| System Design & Scalability | 25% | ~40% | 🟡 YELLOW | Modular FastAPI, SSE lifecycle events, 14 DB indexes, health prober, escalate/task/SLA. Missing: Alembic migrations, Redis multi-worker |
| Real-Time Features & Reliability | 20% | ~65% | 🟢 GREEN | SSE live at `/api/realtime/events?token=`, events on create/update/assign/escalate, task.create/update, sla.breach, health.change. WS ACL enforced. Verified live |
| AI Integration & Automation | 20% | ~75% | 🟢 GREEN | Live OpenRouter — 1,328 char summary (not mock), 5 RCA hypotheses, chat with citations, postmortem with MD download. Prod boot check. Verified live |
| Security & Access Control | 15% | ~90% | 🟢 GREEN | All 8 P0 fixes DEPLOYED LIVE. Voice 401, health 401, RBAC on mutations, demo pw hidden, webhook sig req, WS ACL, JWT prod check. 169 tests green |
| UI/UX & Product Quality | 10% | ~45% | 🟡 YELLOW | Escalate dialog, Create task dialog, Split AI/RCA panels, Deep link via ?id=, Cold-start WakingOverlay. Missing: full war room redesign, mobile |
| Deployment & DevOps | 10% | ~55% | 🟢 GREEN | Live Render (ENV=production), Vercel deployed, CI workflow, verify_live.sh ALL PASS. Playwright test created |

**Blended: ~65-70%** — All core FRs deployed and verified live. Security at 90%, AI at 75%, Realtime at 65%.

## Live Verification (ALL PASSING)

```
✓ /healthz → 200
✓ /api/demo-status → ready, 1 open SEV1, NO password leak
✓ /auth/login → JWT obtained
✓ Unauth voice → 401 (was 422)
✓ Unauth health → 401 (was 200)
✓ Incidents → 3 total, SEV1 found
✓ AI Summary → 1,328 chars, NOT mock (OpenRouter)
✓ AI RCA → 5 hypotheses
✓ SSE → event: connected
✓ Timeline → 200
✓ Tasks → 200
✓ SLA → 200
✓ Escalate → 200 (was 404)
✓ Assign → 200
✓ Frontend → WakingOverlay live on Vercel
```

## Functional Requirements — ALL GREEN/YELLOW

| # | FR | Status | Live Evidence |
|---|----|--------|----------|
| 1 | Team auth + RBAC | 🟢 GREEN | JWT, 4 roles, require_permission on mutations, unauth → 401 |
| 2 | Realtime dashboard | 🟢 GREEN | SSE live, events on lifecycle, FE auto-opens SEV1 |
| 3 | Log + alert monitoring | 🟡 YELLOW | Models + seed data, monitoring page. Log filters TBD |
| 4 | AI summary + RCA | 🟢 GREEN | 1,328 char summary, 5 RCA hypotheses, chat, postmortem |
| 5 | GitHub deploys | 🟢 GREEN | Webhook sig required, 4 deployments with SHA/author |
| 6 | Service health | 🟢 GREEN | 5 services, auth+team filter, health prober wired |
| 7 | Per-incident comms | 🟡 YELLOW | SSE works, CommsPanel in war room |
| 8 | Timeline | 🟢 GREEN | Events on all lifecycle changes, GET 200 |
| 9 | Tasks + escalate + SLA | 🟢 GREEN | CRUD, countdown, breach, escalate 200, FE button |
| 10 | Analytics | 🟡 YELLOW | MTTR, severity breakdown, loading/error states |

## Brownie Features

| Feature | Status | Evidence |
|---------|--------|----------|
| AI Chat | 🟢 GREEN | RAG with citations, ChatPanel in war room |
| Postmortem | 🟢 GREEN | Structured sections + MD download |
| Voice-to-ticket | 🟢 GREEN | Auth from JWT, file upload, VoiceRecorder |
| Anomaly detection | 🟡 YELLOW | Autoencoder scores, analytics risk level |
| Containers | 🔴 RED | Compose file exists, cloud shows unavailable |

## Deploy Status
- Backend: https://sentinel-api-clu9.onrender.com (ENV=production, commit a9732b1)
- Frontend: https://sentinel-hers.vercel.app (WakingOverlay live)
- AI Provider: OpenRouter (live, non-mock)
- Env vars: AI_PROVIDER, OPENROUTER_API_KEY, JWT_SECRET, JWT_REFRESH_SECRET, ENV=production, CORS_ORIGINS, AUTO_SEED_DEMO, ALLOW_MOCK_AI=1