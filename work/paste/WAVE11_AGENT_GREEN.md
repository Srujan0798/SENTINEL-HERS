You are a Tier-2 worker on SENTINEL. Execute ONE task: make the FULL suite green with real fixes. STOP when green. Do not push or deploy.

# LAW
1. Prefer fixing tests + small production bugs. Do not delete product features to fake green.
2. Fail loud. No silent skip of failing tests unless quarantined with reason in report.
3. Run full suite twice if needed. Paste REAL output. No proof = not done.
4. Repo: SENTINEL-HERS. AI_PROVIDER=mock for tests.
5. Write report: work/reports/wave-11/01-suite-green.report.md

# ROOT CAUSES (orchestrator-verified — fix these)

## A. Test isolation poison (main cause of SLA "no such table: incidents")
New files use module-scoped:
  app.dependency_overrides[get_db] = override_db
WITHOUT clearing overrides after the module.
Affected likely: tests/integration/test_postmortem.py, test_containers.py, test_ai_chat.py, and any similar.

FIX:
- Use function-scoped fixtures OR always clear:
  yield
  app.dependency_overrides.clear()
  Base.metadata.drop_all(...)
- Prefer function-scoped DB engines so modules do not clobber each other.
- Pattern: fixture autouse that sets override for the test, then clears.

## B. Containers API contract drift
list_containers / docker client now return dicts with available/reason/containers.
Old test_anomaly.py::test_containers_endpoint and some new container tests may expect list or wrong mock target.

FIX:
- Align tests to new shape: {"docker":{"available":bool,"reason":...,"containers":[]}, "kubernetes":{...}}
- Fix mocks to patch the real symbols used in client modules (module-level _docker / from_env etc.)
- Keep graceful unavailable branch working.

## C. Postmortem tests failing
Route is GET /api/ai/postmortem/{incident_id} (and ?format=md).
Tests may hit wrong method/path, wrong auth headers, or DB isolation issues.

FIX:
- Make tests match real route + auth.
- Ensure create_all includes all tables the endpoint needs.
- Do not require incident "resolved" if product allows open — either relax product rule OR create resolved incidents in fixture (match route code).

## D. Anomaly tests
- Unauthorized score may return wrong code after DB poison — fix isolation first.
- Alert-count / analytics anomalies assertions must match real JSON keys from GET /api/analytics/anomalies.

## E. VCS deployments
- test_list_deployments: ensure webhook creates tenant-scoped deployment readable by same team.
- test_deployments_unauthorized: GET /api/integrations/deployments without token MUST be 401/403 (not 200). If code lacks Depends(auth) on any path, fix production code. If pollution from overrides, fix isolation.

## F. SLA KeyError / no such table
Almost certainly isolation (A). After clearing overrides + proper create_all on SLA's own DB, re-run. Only change SLA production code if still broken in isolation.

# WRITE-SET
- tests/** (especially integration/*)
- src/backend/** only if production bug (auth missing, wrong response shape, postmortem route bug)
- work/reports/wave-11/01-suite-green.report.md

# FORBID
- Deploy configs rewrite for fun
- Deleting WRITEUP/README features
- Skipping entire modules with pytest.mark.skip without written reason

# ACCEPTANCE (required)
```bash
AI_PROVIDER=mock python -m pytest -q
```
Must show **0 failed, 0 errors**. Paste the last summary line (e.g. "N passed").

Also paste:
```bash
AI_PROVIDER=mock python -m pytest tests/integration/test_sla.py tests/integration/test_containers.py tests/integration/test_postmortem.py tests/integration/test_ai_chat.py tests/integration/test_anomaly.py tests/integration/test_vcs_integration.py -q
```
All green.

# REPORT template
# REPORT — wave-11 / 01-suite-green
- Result: DONE | PARTIAL | BLOCKED
## Root causes fixed
## Files changed
## Full suite output (paste)
## Residual risks

Then STOP.
