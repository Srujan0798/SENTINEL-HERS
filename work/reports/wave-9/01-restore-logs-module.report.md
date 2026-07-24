# wave-9 / 01-restore-logs-module — REPORT

## Status: DONE (acceptance green)

Recreated the missing `src/backend/logs/` package so `ingest`, `ai`, and `analytics`
import cleanly and the logs integration tests pass. This was the single module
breaking the whole suite (8 collection errors) — now 0.

## Files created (write-set only — nothing else touched)
- `src/backend/logs/__init__.py` — imports `models` so Base.metadata registers the tables (conftest contract).
- `src/backend/logs/database.py` — mirrors `incidents/database.py`; re-exports `Base/SessionLocal/engine/get_db` from `src.backend.db`.
- `src/backend/logs/models.py` — `LogEntryModel`, `AlertModel` (ORM on shared Base); `LogEntry`, `Alert`, `LogIngest`, `AlertCreate` (Pydantic); `LogLevel` enum; `SeverityLevel` re-exported from `incidents.enums`. Plus `alert_from_orm` helper.
- `src/backend/logs/routes.py` — `router` (APIRouter, no prefix): `GET /api/logs/search`, `GET /api/alerts`, `POST /api/alerts/{alert_id}/resolve`.

## Field contract honored (grep-verified against downstream)
- `AlertModel`: id, team_id, incident_id, source, alert_type, title, description, severity, is_resolved, resolved_at, resolved_by, `metadata_` (Python attr → JSON column named `metadata`), fired_at, created_at.
- `LogEntryModel`: id, team_id, incident_id, service, level, message, `metadata_`, source_ip, indexed_at, created_at (indexed for search timing).
- UUID columns use a local `_UuidStr` TypeDecorator (accepts UUID objects from ingest and str ids from auth/ai tests).

## Notable implementation detail (fail-loud, not a hack)
`LogEntryModel`/`AlertModel` set `__table_args__ = {"implicit_returning": False}`.
Reason: SQLAlchemy's insertmanyvalues RETURNING-sentinel KeyErrors when a
TypeDecorator PK is bulk-inserted with explicit **string** ids (ai_summary test)
whose processed result (UUID) differs from the original str param. Disabling
implicit RETURNING on these two tables makes bulk insert fall back to plain
executemany; downstream code already uses `db.refresh()`, so nothing depends on
RETURNING. Verified both the UUID-input path (ingest) and str-input path (ai) now work.

## Acceptance — verbatim

### pytest
```
$ python -m pytest tests/integration/test_logs.py tests/integration/test_ai_summary.py -q
31 passed, 8 warnings in 4.22s
```

### imports
```
$ python -c "import src.backend.ingest.routes, src.backend.ai.routes, src.backend.analytics.routes; print('imports OK')"
imports OK
```

### full-suite collection (proof the 8 collection errors are gone)
```
$ python -m pytest --collect-only -q
149 tests collected in 0.15s
```

## Deviations / files outside write-set
None. Only the 4 write-set files were created. `tests/`, `ingest/`, `ai/`,
`analytics/`, and everything else were read but not modified.
