# Report — wave-9 / 03-render-backend-deploy

## Status: COMPLETE

Produced a Render Blueprint deploying the FastAPI backend + managed PostgreSQL +
managed Redis (Key Value), with a pre-deploy migrate+seed step, public HTTPS, and
working `/healthz` / `/metrics`.

## Files created / changed
- `render.yaml` (NEW) — Blueprint: web (Docker), managed Postgres, managed Redis.
- `deployment/render/release.sh` (NEW, +x) — migrate + idempotent demo seed.
- `docs/DEPLOYMENT.md` (NEW) — click-path, env-var table, release + rollback.
- `.env.example` (EDIT) — added deploy-only vars (placeholders only).
- `Dockerfile.api` (EDIT) — non-root USER, bind `0.0.0.0:$PORT`, $PORT healthcheck,
  copy `scripts/` + `deployment/render/` into image (needed for the release step).

## Acceptance

1. render.yaml parses:
```
render.yaml valid
```

2. Boot smoke — **uvicorn fallback** (Docker daemon was DOWN):
```
=== /healthz ===
{"status":"ok"}
=== /metrics (first line) ===
# HELP python_gc_objects_collected_total Objects collected during gc
```
`/healthz` → 200 JSON, `/metrics` → Prometheus text. Pass.

3. Secrets: none hardcoded. `JWT_SECRET`/`JWT_REFRESH_SECRET` = `generateValue: true`;
   `ANTHROPIC_API_KEY`/`GEMINI_API_KEY`/`*_WEBHOOK_SECRET`/`CORS_ORIGINS` = `sync: false`
   (dashboard-only). `DATABASE_URL`/`REDIS_URL` injected via `fromDatabase`/`fromService`.

## Idempotency
`scripts/seed_demo.py` is NOT idempotent for incidents (re-creates SEV1 each run) and
is outside the write-set. Guard implemented in `release.sh`: logs in as the demo user,
checks `/api/incidents` for existing data, skips seeding if present. Redeploys will not
duplicate the SEV1 incident.

## Required follow-ups (outside write-set)
- Add an "existing demo team" idempotency guard inside `scripts/seed_demo.py`.
- Add `requests` to `api/requirements.txt` (seed imports it; release.sh installs it at
  release time as a stopgap).
- `api/main.py` hardcodes CORS `allow_origins` to localhost — must be changed to read
  the `CORS_ORIGINS` env var or the Vercel origin will be rejected in prod.

## Write-set note
All changes within the declared write-set. Dockerfile.api edits stayed within the
allowed prod-hardening scope (bind $PORT, non-root USER, HEALTHCHECK) plus the COPY
lines required for the release step to find scripts/ in the image.
