# REPORT — wave-9 / 03b-deploy-hardening

**Status:** DONE (pending orchestrator independent verification)
**Agent:** grok (resume from rate-limited Claude session; 9.3b worker partially complete)

## What changed
- `api/main.py` — `CORS_ORIGINS` env (comma-separated); localhost fallback for dev/tests
- `api/requirements.txt` — `requests>=2.31.0`
- `scripts/seed_demo.py` — early exit when demo team already has incidents (idempotent)
- `deployment/render/release.sh` — dropped temporary pip install of requests; dual guard kept
- `docs/DEPLOYMENT.md` — follow-ups marked resolved
- `.env.example` — documents `CORS_ORIGINS` + frontend base URL

## Acceptance
- CORS reads env; no `*` with credentials
- Seed no-ops on second run when incidents exist
- Full suite still green
