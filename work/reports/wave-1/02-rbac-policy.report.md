# REPORT — wave-1 / 02-rbac-policy

- **Agent:** opencode (mimo-v2.5-pro)
- **Result:** DONE
- **Date:** 2026-06-19

## What I changed
- `src/backend/__init__.py` — package init
- `src/backend/rbac/__init__.py` — package init
- `src/backend/rbac/models.py` — Role enum (owner/responder/viewer) and UserContext Pydantic model
- `src/backend/rbac/policy.py` — Policy table mapping actions → allowed roles, check_permission function
- `src/backend/rbac/dependencies.py` — require_role() and require_permission() FastAPI dependencies
- `tests/integration/__init__.py` — package init
- `tests/integration/test_rbac.py` — 24 integration tests verifying RBAC enforcement

## Acceptance proof (REQUIRED — FM-09)
```
$ python3 -m pytest tests/integration/test_rbac.py -v

============================= test session starts ==============================
platform darwin -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
plugins: Faker-40.15.0, cov-7.1.0, locust-2.43.4, xdist-3.8.0, timeout-2.4.0, asyncio-1.3.0, hypothesis-6.152.2, anyio-4.13.0
asyncio: mode=Mode.STRICT, debug=False
collected 24 items

tests/integration/test_rbac.py::TestViewerPermissions::test_viewer_can_read PASSED
tests/integration/test_rbac.py::TestViewerPermissions::test_viewer_gets_403_on_triage PASSED
tests/integration/test_rbac.py::TestViewerPermissions::test_viewer_gets_403_on_create PASSED
tests/integration/test_rbac.py::TestViewerPermissions::test_viewer_gets_403_on_assign PASSED
tests/integration/test_rbac.py::TestViewerPermissions::test_viewer_gets_403_on_resolve PASSED
tests/integration/test_rbac.py::TestViewerPermissions::test_viewer_gets_403_on_comment PASSED
tests/integration/test_rbac.py::TestViewerPermissions::test_viewer_gets_403_on_delete PASSED
tests/integration/test_rbac.py::TestViewerPermissions::test_viewer_gets_403_on_escalate PASSED
tests/integration/test_rbac.py::TestResponderPermissions::test_responder_can_read PASSED
tests/integration/test_rbac.py::TestResponderPermissions::test_responder_can_triage PASSED
tests/integration/test_rbac.py::TestResponderPermissions::test_responder_can_create PASSED
tests/integration/test_rbac.py::TestResponderPermissions::test_responder_can_assign PASSED
tests/integration/test_rbac.py::TestResponderPermissions::test_responder_can_resolve PASSED
tests/integration/test_rbac.py::TestResponderPermissions::test_responder_can_comment PASSED
tests/integration/test_rbac.py::TestResponderPermissions::test_responder_gets_403_on_delete PASSED
tests/integration/test_rbac.py::TestResponderPermissions::test_responder_gets_403_on_escalate PASSED
tests/integration/test_rbac.py::TestOwnerPermissions::test_owner_can_read PASSED
tests/integration/test_rbac.py::TestOwnerPermissions::test_owner_can_triage PASSED
tests/integration/test_rbac.py::TestOwnerPermissions::test_owner_can_create PASSED
tests/integration/test_rbac.py::TestOwnerPermissions::test_owner_can_assign PASSED
tests/integration/test_rbac.py::TestOwnerPermissions::test_owner_can_resolve PASSED
tests/integration/test_rbac.py::TestOwnerPermissions::test_owner_can_comment PASSED
tests/integration/test_rbac.py::TestOwnerPermissions::test_owner_can_delete PASSED
tests/integration/test_rbac.py::TestOwnerPermissions::test_owner_can_escalate PASSED

============================== 24 passed in 3.39s ==============================
```

## Deviations from brief
- none

## Gotchas hit (→ orchestrator adds to docs/waves/wave-<N>-gotchas.md)
- Auth module (01-auth-backend) doesn't exist yet. Used dependency injection pattern with placeholder `_get_current_user_placeholder` that auth module will override via `app.dependency_overrides`. This is the intended integration point.

## Follow-ups / parked (→ BACKLOG)
- 01-auth-backend needs to wire `get_current_user` dependency and override the placeholder
- Policy table can be extended with more granular permissions as features are added
- Consider adding team-scoping enforcement (currently RBAC is role-only, team isolation is separate)
