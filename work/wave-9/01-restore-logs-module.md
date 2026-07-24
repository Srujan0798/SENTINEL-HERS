# TASK — wave-9 / 01-restore-logs-module

> Self-contained brief. The worker needs NOTHING outside this file + the repo.
> Worker uses its OWN skills. Does NOT plan beyond this task. Writes ONLY to the write-set below.

## Goal (one sentence)
Recreate the **missing** `src/backend/logs/` package so that `ingest`, `ai`, and `analytics` import
cleanly and `tests/integration/test_logs.py` passes — this single module currently breaks the ENTIRE
test suite (8 collection errors).

## Context (just enough)
- Wave: 9 — Submission Hardening
- Depends on (already merged): wave-0 db layer (`src/backend/db.py` exposes `Base, SessionLocal, engine, get_db`)
- **Why this exists:** Wave-3 `01-log-ingestion` was marked SHIPPED but the `logs` package was never
  committed (FM-09 false status). Everything that imports it is dead until you restore it.
- **The contract is the failing test** — `tests/integration/test_logs.py` is the exact API you must satisfy.
  Read it first; it defines endpoints, status codes, and payload shapes.

### Exact symbols the codebase imports from this module (grep-verified — all MUST exist)
From `src.backend.logs.database`: `get_db`, `SessionLocal`, `engine`
From `src.backend.logs.models`:
  `LogEntryModel`, `AlertModel` (SQLAlchemy ORM on `Base`),
  `LogEntry`, `Alert`, `LogIngest`, `AlertCreate` (Pydantic schemas),
  `LogLevel`, `SeverityLevel` (enums)
From `src.backend.logs.routes`: `router` (APIRouter)

### Field contract (reverse-engineered from `ingest/routes.py` + `analytics/routes.py` — do not drift)
- `AlertModel` columns used downstream: `id, team_id, incident_id, source, alert_type, title,
  description, severity, is_resolved, resolved_at, resolved_by, metadata_` (Python attr `metadata_`
  mapping to a `metadata` JSON column), `fired_at, created_at`.
- `LogEntryModel` columns used downstream: `id, team_id, service, level, message, timestamp/created_at,
  metadata_` (+ whatever `test_logs.py` asserts on search — read it).
- Mirror the DB wiring pattern in `src/backend/incidents/database.py` exactly (re-export from `db.py`).

## Write-set (you may ONLY create/edit these — FM-13)
- `src/backend/logs/__init__.py`
- `src/backend/logs/database.py`
- `src/backend/logs/models.py`
- `src/backend/logs/routes.py`

## Forbid-set (do NOT touch)
- `src/backend/ingest/`, `src/backend/ai/`, `src/backend/analytics/` — they already import your module correctly; do NOT edit them to match yourself. Match THEM.
- `tests/` — the tests are the spec. Make them pass; do not weaken them.
- everything else, especially other agents' write-sets and shared root config

## Blast radius
r1 — write src. Auto.

## Steps
1. Read `tests/integration/test_logs.py` end-to-end — it is your acceptance contract (ingest → search → alert CRUD).
2. Read `src/backend/ingest/routes.py` and `src/backend/analytics/routes.py` to capture every attribute they read off `LogEntryModel`/`AlertModel`.
3. Read `src/backend/incidents/{database,models,routes}.py` as the structural template to mirror (naming, Base usage, session handling, router style).
4. Write `logs/database.py` (re-export `Base, SessionLocal, engine, get_db` from `src.backend.db`, mirror `incidents/database.py`).
5. Write `logs/models.py` — ORM models + Pydantic schemas + enums, with EXACT names/fields above.
6. Write `logs/routes.py` — the log search + alert CRUD endpoints that `test_logs.py` exercises.
7. Write `logs/__init__.py` (import models so `from src.backend.logs import models` works — see `tests/conftest.py`).
8. Run acceptance. Iterate until green. Fail loud — no `except: pass`.

## Acceptance (must produce PROOF — FM-09)
- Command: `python -m pytest tests/integration/test_logs.py tests/integration/test_ai_summary.py -q`
- Expected: all tests in both files **pass**, 0 errors, 0 collection errors.
- Also run: `python -c "import src.backend.ingest.routes, src.backend.ai.routes, src.backend.analytics.routes; print('imports OK')"` → must print `imports OK`.
- Paste BOTH command outputs verbatim into your report. No "done" without it.

## Guardrails to obey
- FM-09 no false status · FM-11 fail loud, no swallowed errors · FM-08 no scope creep (logs module only)
- Do NOT edit the tests or the importing modules to make yourself pass — YOU conform to THEM.
- Seed any data via the API in the test; never inject synthetic rows to fake a pass.

## Report to
`work/reports/wave-9/01-restore-logs-module.report.md` (use REPORT_TEMPLATE.md)
