# TASK — wave-1 / 02-rbac-policy

## Goal
Role-based access control: owner / responder / viewer enforced on every protected route.

## Context
- Wave: 1. Depends on wave-0. Coordinates with 01-auth-backend via the JWT role claim (read-only of its interface).

## Write-set (ONLY these)
- src/backend/rbac/
- tests/integration/test_rbac.py

## Forbid-set
- src/backend/auth/ (mistral owns — consume its `get_current_user`, do not edit it)

## Blast radius
r1.

## Roles & matrix
- **owner**: all. **responder**: triage/assign/resolve/comment. **viewer**: read-only.

## Steps
1. `require_role(*roles)` dependency / decorator.
2. Policy table mapping action → allowed roles.
3. Apply to representative routes; under-privileged call → 403.

## Acceptance (PROOF — FM-09)
- Command: `pytest tests/integration/test_rbac.py -v`
- Expected: viewer gets 403 on write routes; responder allowed on triage; owner allowed everywhere.

## Report to
`work/reports/wave-1/02-rbac-policy.report.md`
