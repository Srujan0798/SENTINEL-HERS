# TASK — wave-9 / 02-green-test-suite

> Self-contained brief. The worker needs NOTHING outside this file + the repo.

## Goal (one sentence)
Make the **entire** test suite pass deterministically (`python -m pytest -q` → all green) on the
pinned runtime, fixing any collection/runtime/isolation failures that remain after the logs module lands.

## Context (just enough)
- Wave: 9 — Submission Hardening
- **Depends on (must be merged first): wave-9/01-restore-logs-module.** Do not start until it is green.
- There are **150 test functions** across `tests/unit`, `tests/integration`, `tests/performance`.
- EXECUTION.md previously claimed "146 passing" — that status was false on a clean checkout. Your job
  is to make it TRUE and reproducible from a fresh venv.
- Known noise to resolve or justify: Pydantic v2 `class Config` deprecation warnings; a Starlette
  TestClient/httpx deprecation; possible Python-version drift (project targets 3.11 — see below).

## Runtime pin (do this first — removes a whole class of "works on my machine")
- Create/verify `api/requirements.txt` installs clean, and ensure tests run under **Python 3.11**
  (the declared stack). If the local default is 3.14, create the venv with 3.11 explicitly.
- Add `pytest` + `pytest-asyncio` to `api/requirements.txt` (currently missing — tests can't run without them).
- Document the exact commands in your report.

## Write-set (you may ONLY create/edit these — FM-13)
- `tests/**` (fixtures, conftest, isolation fixes ONLY — do NOT weaken assertions)
- `api/requirements.txt` (add pytest/pytest-asyncio + any missing test dep)
- `pytest.ini` (if a marker/config fix is needed)
- `src/backend/**/*.py` — ONLY minimal, surgical fixes to genuine bugs the tests expose (e.g. a
  Pydantic v2 `class Config` → `model_config = ConfigDict(...)` migration). If a fix is larger than
  a few lines or changes behavior, STOP and report BLOCKED with the specifics.

## Forbid-set (do NOT touch)
- Do NOT delete or `xfail`/`skip` tests to get green. A skipped test is not a passing test (FM-09).
- Do NOT touch deploy config, frontend, or docs.

## Blast radius
r1 — write src/tests. Auto.

## Steps
1. Fresh venv on Python 3.11, `pip install -r api/requirements.txt`.
2. `python -m pytest -q` — capture the full failure list.
3. Fix causes in dependency order (imports → models → isolation → assertions-that-reveal-real-bugs).
4. Address cross-module DB contamination the same way `test_auth.py::reset_db` already does (see EXECUTION.md note about replacing `auth_service.db` via module attribute).
5. Re-run until 100% green, twice in a row (catch flakiness — FM-10).

## Acceptance (must produce PROOF — FM-09)
- Command: `python -m pytest -q`
- Expected: `N passed` where N == total collected (currently 150), `0 failed`, `0 errors`, `0` unexpected skips.
- Run it **twice** and paste both outputs (proves non-flaky, FM-10).
- Paste the exact Python version (`python --version`) and pip freeze diff if you changed deps.

## Guardrails to obey
- FM-09 no false status · FM-10 no flaky tests · FM-11 fail loud · FM-08 minimal surgical fixes only
- Green by fixing code/fixtures, NEVER by weakening tests.

## Report to
`work/reports/wave-9/02-green-test-suite.report.md`
