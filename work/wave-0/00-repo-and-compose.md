# TASK — wave-0 / 00-repo-and-compose

## Goal
Stand up the monorepo skeleton, Docker Compose stack, and CI so every later wave has a one-command boot.

## Context
- Wave: 0 — Foundation & Contracts (THE SPINE). Run this FIRST, alone.
- Depends on: none.
- Stack: Next.js 15 frontend, FastAPI backend, PostgreSQL (Supabase-compatible), Redis, Prometheus.

## Write-set (ONLY these)
- docker-compose.yml
- Dockerfile.api
- Dockerfile.frontend
- Makefile
- .env.example
- .github/workflows/ci.yml
- README scaffolding for `make` targets only (append, don't rewrite)

## Forbid-set
- src/** (other agents own feature code), schema/** (deep owns it), frontend/ui (qwen owns it)

## Blast radius
r1 — local repo.

## Steps
1. Compose services: `frontend`, `api`, `postgres`, `redis`, `prometheus`. Healthchecks on each.
2. `Dockerfile.api` (python:3.11-slim, uvicorn) exposing `/healthz`. `Dockerfile.frontend` (node, next).
3. `Makefile` targets: `up`, `down`, `logs`, `test`, `seed`, `worker-N`.
4. `.env.example` with every key referenced (DB, REDIS, AI provider keys placeholders — NO real secrets, FM-07).
5. `ci.yml`: lint + test + `docker compose build`.

## Acceptance (PROOF required — FM-09)
- Command: `docker compose up --build -d && curl -fsS localhost:8000/healthz`
- Expected: `{"status":"ok"}` (a stub `/healthz` is fine for this task).

## Report to
`work/reports/wave-0/00-repo-and-compose.report.md`
