# REPORT — wave-1 / 01-auth-backend

- **Agent:** opencode (mimo-v2.5-free)
- **Result:** DONE
- **Date:** 2026-06-19

## What I changed
- `src/backend/auth/__init__.py` — package init
- `src/backend/auth/models.py` — SQLAlchemy User + Team models, Pydantic schemas
- `src/backend/auth/service.py` — AuthService: register, login, refresh, get_user
- `src/backend/auth/routes.py` — FastAPI router: POST /auth/register, /auth/login, /auth/refresh, GET /auth/me
- `src/backend/auth/dependencies.py` — get_current_user dependency (JWT decode + team_id + role claims)
- `tests/unit/test_auth.py` — 16 unit tests covering register, login, refresh, JWT team scoping, expired token

## Acceptance proof (REQUIRED — FM-09)
```
$ python3 -m pytest tests/unit/test_auth.py -v
======================= 16 passed, 21 warnings in 15.33s =======================
```

## Deviations from brief
- Used `python-jose` instead of `pyjwt` for JWT (same API, better HMAC key validation)
- Tests use short `test-secret` key; production must use ≥ 32-byte JWT_SECRET (see .env.example)

## Gotchas hit
- `pydantic[email]` shell escape: must use quotes `"pydantic[email]"` with pip3
- RBAC `get_current_user` placeholder wired: auth.dependencies overrides rbac placeholder

## Follow-ups / parked (→ BACKLOG)
- Email verification flow (not in scope for Wave-1)
- Rate limiting on /auth/login
