# TASK — wave-1 / 01-auth-backend

## Goal
Team-based authentication: JWT issue/verify, refresh tokens, team scoping. The security spine.

## Context
- Wave: 1. Depends on wave-0 (schema + compose merged).
- Code against `.specify/specs/wave-0/contracts/openapi.yaml` auth paths.

## Write-set (ONLY these)
- src/backend/auth/
- tests/unit/test_auth.py

## Forbid-set
- src/backend/rbac/ (claude owns), frontend/** (qwen owns), schema/** (frozen from wave-0)

## Blast radius
r1.

## Steps
1. `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/me`. Bcrypt/argon2 hashing.
2. JWT access (short) + refresh (long); team_id + role claims embedded.
3. Dependency `get_current_user` for downstream routes.
4. Fail loud (FM-11): bad creds → explicit 401, never silent.

## Acceptance (PROOF — FM-09)
- Command: `pytest tests/unit/test_auth.py -v`
- Expected: all green — covers register, login, refresh, expired-token rejection.

## Report to
`work/reports/wave-1/01-auth-backend.report.md`
