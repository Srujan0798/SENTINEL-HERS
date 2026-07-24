# TASK — wave-9 / 03-render-backend-deploy

> Self-contained brief. The worker needs NOTHING outside this file + the repo.

## Goal (one sentence)
Produce a **Render Blueprint** (`render.yaml`) that deploys the FastAPI backend + managed PostgreSQL +
managed Redis, runs DB migrations and the demo seed on release, and exposes a public HTTPS URL with a
working `/healthz` and `/metrics` — this is a MANDATORY submission artifact (live deployment URL).

## Context (just enough)
- Wave: 9 — Submission Hardening. Decision locked: **Render (backend) + Vercel (frontend)**.
- **Depends on: wave-9/01-restore-logs-module** (backend can't even boot without it — `main.py` imports `ingest` → `logs`).
- Existing assets to build on: `Dockerfile.api`, `docker-compose.yml`, `api/main.py`, `api/startup.py`,
  `scripts/seed_demo.py`, `deployment/prometheus/`, `deployment/grafana/`.
- The app is sqlite+postgres compatible; in cloud it MUST use the Render Postgres `DATABASE_URL`.

## Write-set (you may ONLY create/edit these — FM-13)
- `render.yaml` (new — Blueprint: web service + Postgres + Redis)
- `Dockerfile.api` (edits ONLY if needed for prod: non-root user, `$PORT` binding, healthcheck)
- `deployment/render/` (any helper scripts, e.g. `release.sh` for migrate+seed)
- `docs/DEPLOYMENT.md` (new — exact click-path + env-var list + rollback)
- `.env.example` (add any new deploy-only vars, values REDACTED)

## Forbid-set (do NOT touch)
- `src/backend/**` app logic (only wire config/env; no feature edits)
- Frontend, tests, other deploy targets

## Blast radius
r3 (creates external deploy config; actual `render deploy` is the human's click). Config = auto; the
human performs the live deploy. Do NOT commit any real secret — Render env vars are set in dashboard.

## Steps
1. Read `api/main.py`, `api/startup.py`, `Dockerfile.api`, `docker-compose.yml` to learn the boot contract, port, and env vars.
2. Write `render.yaml`:
   - `web` service from `Dockerfile.api`, binds `0.0.0.0:$PORT`, health check path `/healthz`.
   - `pserv`/managed **PostgreSQL** → inject `DATABASE_URL`.
   - managed **Redis** → inject `REDIS_URL`.
   - env vars: `JWT_SECRET` (generateValue), `ANTHROPIC_API_KEY`/`GEMINI_API_KEY` (sync:false — set in dashboard), `CORS_ORIGINS` (Vercel URL — coordinate with wave-9/04).
   - release command: run migrations then `python scripts/seed_demo.py` (idempotent — must not double-seed on redeploy).
3. Ensure `Dockerfile.api` binds `$PORT`, runs as non-root, has a HEALTHCHECK.
4. Write `docs/DEPLOYMENT.md`: step-by-step "New Blueprint → connect repo → set secrets → deploy", the full env-var table, and how to roll back.
5. Make the seed idempotent (guard on existing demo team) so redeploys don't duplicate the SEV1 incident.

## Acceptance (must produce PROOF — FM-09)
- Command (local prod-parity smoke): `docker build -f Dockerfile.api -t sentinel-api . && docker run --rm -e PORT=8000 -e DATABASE_URL=sqlite:///./smoke.db -e JWT_SECRET=smoke -p 8000:8000 sentinel-api & sleep 8 && curl -fsS localhost:8000/healthz && curl -fsS localhost:8000/metrics | head -1`
- Expected: healthz returns 200 JSON; `/metrics` returns Prometheus text. Paste both.
- Validate `render.yaml` parses: paste `python -c "import yaml,sys; yaml.safe_load(open('render.yaml')); print('render.yaml valid')"`.
- In your report, paste the DEPLOYMENT.md env-var table so the orchestrator can verify no secret is hardcoded.

## Guardrails to obey
- FM-07 no secrets in git (all keys via dashboard, `sync:false`) · FM-11 fail loud on missing env
- FM-09 prove the container boots and serves `/healthz` locally before claiming deployability.

## Report to
`work/reports/wave-9/03-render-backend-deploy.report.md`
