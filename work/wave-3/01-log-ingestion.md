# TASK — wave-3 / 01-log-ingestion

## Goal
Centralised log + alert ingestion endpoint with indexed full-text search < 500ms.

## Context
- Wave: 3. Parallel to wave-2. Schema: `log_entries`, `alerts` tables in `schema/migrations/001_initial_schema.sql`.
- Auth via `src/backend/auth/` `get_current_user`.

## Write-set (ONLY these)
- src/backend/logs/
- src/backend/ingest/

## Forbid-set
- src/backend/health/ (deep owns), src/backend/incidents/ (kimi owns), frontend/**

## Blast radius
r1.

## Steps
1. SQLAlchemy models for `LogEntry`, `Alert`.
2. `POST /api/ingest/logs` — bulk ingest (up to 1000 entries per call); validates schema, stores with `team_id` + `source` + `ts`.
3. `POST /api/ingest/alerts` — single alert creation; emits `alert.created` to realtime hub.
4. `GET /api/logs/search?q=&service=&level=&from=&to=` — pg_trgm full-text search, < 500ms on 100k rows.
5. `GET /api/alerts` — list with filter by status (open/resolved) + service.
6. `PATCH /api/alerts/{id}/resolve` — resolve alert with resolution notes.
7. Fail loud (FM-11): malformed log entry → 422 with details; never silently drop.

## Acceptance (PROOF — FM-09)
```
pytest tests/integration/test_logs.py -v
# Expected: ingest, search, alert CRUD all green; search timing assertion < 500ms on seeded 10k rows
```

## Report to
`work/reports/wave-3/01-log-ingestion.report.md`
