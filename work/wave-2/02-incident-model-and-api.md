# TASK — wave-2 / 02-incident-model-and-api

## Goal
Incident CRUD API with SEV1-4 severity enum and triage state machine. The core domain object.

## Context
- Wave: 2. Schema is in `schema/migrations/001_initial_schema.sql`. OpenAPI in `.specify/specs/wave-0/contracts/openapi.yaml`.
- Auth via `src/backend/auth/` `get_current_user`; RBAC via `src/backend/rbac/` `require_role`.

## Write-set (ONLY these)
- src/backend/incidents/
- tests/integration/test_incidents.py

## Forbid-set
- src/backend/auth/, src/backend/rbac/, src/backend/realtime/ (other agents own)

## Blast radius
r1.

## Steps
1. SQLAlchemy models for `Incident`, `TimelineEvent` (with `source, actor, ts` provenance columns).
2. FastAPI router: `POST /api/incidents`, `GET /api/incidents`, `GET /api/incidents/{id}`, `PATCH /api/incidents/{id}` (triage state machine: detected→triaging→investigating→mitigating→resolved→closed), `POST /api/incidents/{id}/assign`.
3. Severity enum: SEV1 (critical), SEV2 (major), SEV3 (minor), SEV4 (informational).
4. Publish to realtime hub on every state change: `await hub.publish(team_id, "incident.updated", {...})`.
5. Emit a timeline event for every state transition (actor + source + ts).
6. Fail loud (FM-11): invalid state transition → explicit 422.

## Acceptance (PROOF — FM-09)
```
pytest tests/integration/test_incidents.py -v
# Expected: all green — create, list, get, triage transitions, assign, invalid transition rejected
```

## Report to
`work/reports/wave-2/02-incident-model-and-api.report.md`
