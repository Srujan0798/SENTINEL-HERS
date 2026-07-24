#!/usr/bin/env bash
#
# SENTINEL — Render pre-deploy release step.
# 1. Apply DB migrations (create_all — idempotent).
# 2. Ensure demo seed via POST /api/seed (idempotent).
set -euo pipefail

log() { echo "[release] $*"; }

log "starting release: migrations + demo seed"

log "applying DB migrations"
python -c "from api.startup import run_migrations; run_migrations()"

SEED_PORT="${SEED_PORT:-8099}"
log "booting local API on 127.0.0.1:${SEED_PORT} for seeding"
uvicorn api.main:app --host 127.0.0.1 --port "${SEED_PORT}" >/tmp/seed-api.log 2>&1 &
APP_PID=$!
trap 'kill "${APP_PID}" 2>/dev/null || true' EXIT

for _ in $(seq 1 45); do
  if curl -fsS "http://127.0.0.1:${SEED_PORT}/healthz" >/dev/null 2>&1; then break; fi
  sleep 1
done
if ! curl -fsS "http://127.0.0.1:${SEED_PORT}/healthz" >/dev/null 2>&1; then
  log "ERROR: local API did not become healthy — seed log follows"
  cat /tmp/seed-api.log || true
  exit 1
fi
log "local API healthy"

SECRET="${SEED_SECRET:-sentinel-seed-dev-only}"
log "ensuring demo seed via /api/seed"
CODE=$(curl -sS -o /tmp/seed-out.json -w "%{http_code}" \
  -X POST "http://127.0.0.1:${SEED_PORT}/api/seed" \
  -H "X-Seed-Secret: ${SECRET}" \
  -H "Content-Type: application/json" || true)
log "seed HTTP ${CODE}: $(cat /tmp/seed-out.json 2>/dev/null || true)"
if [[ "${CODE}" != "200" && "${CODE}" != "201" ]]; then
  log "WARN: seed step non-OK (non-fatal) — app will still promote; AUTO_SEED_DEMO on boot will retry"
fi

log "release step done"
