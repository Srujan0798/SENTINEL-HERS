#!/usr/bin/env bash
#
# SENTINEL — Render pre-deploy release step.
# Runs in the built image (Dockerfile.api) with DATABASE_URL / REDIS_URL injected,
# BEFORE the new web version is promoted. Responsibilities:
#   1. Apply DB migrations (create_all — idempotent).
#   2. Seed the demo dataset (SEV1 incident + timeline + tasks) ONCE.
#
# The seed (scripts/seed_demo.py) drives the app over HTTP, so we boot a short-lived
# local uvicorn against the SAME managed Postgres, seed through it, then shut it down.
#
# Idempotency (FM-13 / task requirement): scripts/seed_demo.py is NOT idempotent for
# incidents (it re-creates the SEV1 every run) and is outside this task's write-set,
# so we guard HERE — if the demo team already has incidents we skip seeding entirely.
# Follow-up: add the guard inside scripts/seed_demo.py itself.
#
# Fail loud (FM-11): migrations failing aborts the release. A seed failure is logged
# loudly but does not block promotion (the demo data is best-effort on top of a healthy app).
set -euo pipefail

log() { echo "[release] $*"; }

log "starting release: migrations + demo seed"

# scripts/seed_demo.py imports `requests`, which is NOT in api/requirements.txt
# (requirements.txt is outside this task's write-set). Install it tolerantly here.
# Follow-up: add `requests` to api/requirements.txt so this line can be removed.
pip install --no-cache-dir --user requests >/dev/null 2>&1 || log "WARN: could not install requests"

# 1. Migrations — explicit and fail-loud (also runs on app boot, but we want a hard gate here).
log "applying DB migrations"
python -c "from api.startup import run_migrations; run_migrations()"

# 2. Boot a short-lived local API so the HTTP-based seed can reach it.
SEED_PORT="${SEED_PORT:-8099}"
log "booting local API on 127.0.0.1:${SEED_PORT} for seeding"
uvicorn api.main:app --host 127.0.0.1 --port "${SEED_PORT}" >/tmp/seed-api.log 2>&1 &
APP_PID=$!
trap 'kill "${APP_PID}" 2>/dev/null || true' EXIT

# Wait for health (up to ~30s).
for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${SEED_PORT}/healthz" >/dev/null 2>&1; then break; fi
  sleep 1
done
if ! curl -fsS "http://127.0.0.1:${SEED_PORT}/healthz" >/dev/null 2>&1; then
  log "ERROR: local API did not become healthy — seed log follows"
  cat /tmp/seed-api.log || true
  exit 1
fi
log "local API healthy"

export SENTINEL_URL="http://127.0.0.1:${SEED_PORT}"

# 3. Idempotency guard — skip seeding if the demo team already has incidents.
ALREADY=$(python - <<'PY'
import os, requests
base = os.environ["SENTINEL_URL"]
try:
    r = requests.post(f"{base}/auth/login",
                      json={"email": "demo@sentinel.io", "password": "Sentinel2026!"},
                      timeout=10)
    if not r.ok:
        print("no"); raise SystemExit
    d = r.json()
    tok, team = d["access_token"], d["user"]["team_id"]
    inc = requests.get(f"{base}/api/incidents",
                       headers={"Authorization": f"Bearer {tok}"},
                       params={"team_id": team}, timeout=10)
    body = inc.json() if inc.ok else {}
    n = len(body.get("data", [])) if isinstance(body, dict) else 0
    print("yes" if n > 0 else "no")
except SystemExit:
    print("no")
except Exception:
    print("no")
PY
)

if [ "${ALREADY}" = "yes" ]; then
  log "demo data already present — skipping seed (idempotent redeploy)"
else
  log "seeding demo dataset"
  if python scripts/seed_demo.py; then
    log "seed complete"
  else
    log "WARN: seed step failed (non-fatal) — app will still promote"
  fi
fi

log "release step done"
