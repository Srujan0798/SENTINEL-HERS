# Hall of Shame — Failure Pattern Archive

> Records failure patterns so they are never repeated. Learning tool, not blame tool.

## Pattern 1: "SHIPPED" wave with a missing core module + false green test count

- **Date:** 2026-07-23
- **Test / Component:** `src/backend/logs/` (missing package); `tests/integration/test_logs.py`,
  `test_ai_summary.py`, `test_anomaly.py`, `test_comms.py`, `test_incidents.py`, `test_sla.py`,
  `test_vcs_integration.py`, `test_voice.py` (8 collection errors).
- **Severity:** Critical
- **Root cause:** Wave-3 task `01-log-ingestion` was recorded as SHIPPED in EXECUTION.md and its report
  filed, but the `src/backend/logs/` package (`database.py`, `models.py`, `routes.py`, `__init__.py`)
  was **never committed to git** (`git log -- src/backend/logs/` is empty). Downstream modules
  (`ingest`, `ai`, `analytics`) and 8 test files import it, so the ENTIRE suite fails at collection.
  EXECUTION.md nonetheless claimed "146 passing" — a status that was never true on a clean checkout.
- **Impact:** Backend cannot boot (`main.py` → `ingest` → `logs`). Suite un-runnable. A "complete"
  project was one import away from a non-starting demo. Classic FM-09 (false status) + FM-14 (the
  stale HANDOFF hid it by claiming the opposite — that nothing was built).
- **Fix:** wave-9/01-restore-logs-module recreates the package to satisfy the existing import contract
  and `test_logs.py`; wave-9/02 greens the full suite from a fresh venv. (Commit hashes: TBD on merge.)
- **Prevention:**
  1. A wave is not SHIPPED until acceptance runs from a **clean checkout/fresh venv** — never trust a
     worker's local "passed". Orchestrator re-runs acceptance independently before marking SHIPPED (FM-09).
  2. Add CI (`.github/workflows/ci.yml`) that runs `pytest -q` on a clean container so a missing/uncommitted
     module fails the build immediately.
  3. Never let HANDOFF.md and EXECUTION.md disagree on active state (FM-01) — a drift check should gate merges.
  4. `git status` + `git ls-files src/backend/<module>/` verification as part of every merge.
