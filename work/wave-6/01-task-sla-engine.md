# TASK — wave-6 / 01-task-sla-engine

## Goal
Task assignment engine + SLA-aware timers with auto-escalation on breach. Respects RBAC.

## Context
- Wave: 6. Depends on wave-1 (RBAC) + wave-2 (incidents). Schema: `tasks`, `slas` tables.
- SLA timers run in background (APScheduler or asyncio); breach triggers escalation + realtime event.

## Write-set (ONLY these)
- src/backend/tasks/
- src/backend/sla/
- tests/integration/test_sla.py

## Forbid-set
- src/backend/comms/ (02 owns), src/backend/incidents/, frontend/**

## Blast radius
r1.

## Steps
1. `tasks/`: SQLAlchemy Task model + CRUD. `POST /api/incidents/{id}/tasks` (create), `PATCH /api/tasks/{id}` (update/assign), `GET /api/incidents/{id}/tasks`.
   - Assignment: `require_permission("tasks:create")`.
   - Auto-assign: if incident SEV1/SEV2 and no assignee within 5min → escalate to owner.
2. `sla/`: SLA policy config (SEV1: 15min, SEV2: 1hr, SEV3: 4hr, SEV4: 24hr response SLO).
   - Background checker: every 60s, scan open incidents, compute time-to-SLA-breach.
   - On breach: `PATCH incident.sla_breached=true` + emit `sla.breached` realtime event + escalate (assign to owner if unassigned).
3. `GET /api/sla` — list SLA status per incident (time remaining / breached).

## Acceptance (PROOF — FM-09)
```
pytest tests/integration/test_sla.py -v
# Expected: task CRUD, SLA timer computes correctly, breach triggers escalation
```

## Report to
`work/reports/wave-6/01-task-sla-engine.report.md`
