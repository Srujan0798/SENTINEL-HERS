# REPORT — wave-2 / 02-incident-model-and-api

- **Agent:** opencode (Tier-2 worker)
- **Result:** DONE
- **Date:** 2025-06-19

## What I changed
- `src/backend/incidents/__init__.py` — module init
- `src/backend/incidents/enums.py` — SeverityLevel (SEV1-4), IncidentStatus (6 states), state machine validation
- `src/backend/incidents/database.py` — SQLAlchemy engine/session setup with SQLite test support
- `src/backend/incidents/models.py` — ORM models for Incident + TimelineEvent with provenance columns
- `src/backend/incidents/schemas.py` — Pydantic request/response schemas
- `src/backend/incidents/service.py` — CRUD operations, state machine logic, timeline event emission
- `src/backend/incidents/routes.py` — FastAPI router with 6 endpoints
- `tests/integration/test_incidents.py` — 14 integration tests
- `api/main.py` — wired incident router

## Acceptance proof (REQUIRED — FM-09)
```
$ python3 -m pytest tests/integration/test_incidents.py -v
============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
collecting ... collected 14 items

tests/integration/test_incidents.py::test_create_incident PASSED         [  7%]
tests/integration/test_incidents.py::test_list_incidents PASSED          [ 14%]
tests/integration/test_incidents.py::test_list_incidents_filter_severity PASSED [ 21%]
tests/integration/test_incidents.py::test_get_incident PASSED            [ 28%]
tests/integration/test_incidents.py::test_get_incident_not_found PASSED  [ 35%]
tests/integration/test_incidents.py::test_triage_state_machine_full_cycle PASSED [ 42%]
tests/integration/test_incidents.py::test_invalid_state_transition PASSED [ 50%]
tests/integration/test_incidents.py::test_invalid_transition_from_closed PASSED [ 57%]
tests/integration/test_incidents.py::test_assign_incident PASSED         [ 64%]
tests/integration/test_incidents.py::test_assign_incident_not_found PASSED [ 71%]
tests/integration/test_incidents.py::test_timeline_events_created_on_transitions PASSED [ 78%]
tests/integration/test_incidents.py::test_timeline_provenance_columns PASSED [ 85%]
tests/integration/test_incidents.py::test_update_incident_fields PASSED  [ 92%]
tests/integration/test_incidents.py::test_skip_triage_direct_investigating PASSED [100%]

============================== 14 passed ==============================
```

## Deviations from brief
- Used generic SQLAlchemy types (String, JSON) instead of PostgreSQL-specific types (PG_UUID, JSONB, Enum) to support SQLite testing. Production deployment should use PostgreSQL with native types.
- Used query params for `team_id` and `actor` instead of extracting from JWT auth, since auth module is not yet wired to the incident router.

## Gotchas hit (→ orchestrator adds to docs/waves/wave-2-gotchas.md)
- SQLite doesn't support Python UUID objects natively — all UUIDs must be converted to strings before passing to SQLAlchemy.
- The `validate_transition` function expects IncidentStatus enum objects but the database stores string values — need to convert between them.

## Follow-ups / parked (→ BACKLOG)
- Wire auth dependency (`get_current_user`) to extract `team_id` and `actor` from JWT token
- Add RBAC guards using `require_permission("incidents:create")` etc.
- Realtime hub integration is stubbed — needs `src/backend/realtime/hub.py` to exist
- Consider adding pagination to timeline endpoint
