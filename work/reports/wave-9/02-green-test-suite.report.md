# wave-9 / 02-green-test-suite — Report

## Result
`python -m pytest -q` is fully green, reproducibly, twice in a row.

- Run #1: `149 passed, 7905 warnings in 43.32s` — 0 failed, 0 errors, 0 skips.
- Run #2: `149 passed, 7905 warnings in 39.37s` — 0 failed, 0 errors, 0 skips (non-flaky).
- `python --version` → `Python 3.14.3`

(The 7905 warnings are pre-existing Pydantic V2 / Starlette deprecation warnings, unrelated to this task.)

## What was broken

### The 7 anomaly ERRORS — ONE root cause
The starting `1 failed, 141 passed, 7 errors` had two intertwined problems that
turned out to share a single trigger.

**Actual root cause: `src/backend/sla/policy.py` imported `pytz`, which is not
installed.** `time_remaining_minutes()` did `import pytz` inside its naive-datetime
branch. The `/api/sla` endpoint raised an uncaught `ModuleNotFoundError` mid-request.
Because every integration test shares the module-level Starlette `TestClient`
(and its anyio portal), an uncaught exception inside one request poisoned the
shared portal/app state, cascading into **setup ERRORs** for later tests whose
`auth` fixture calls `client.post("/auth/register")`. Those manifested as the 7
"errors" in `test_anomaly.py` even though the anomaly code itself was fine — run
in isolation each anomaly test passed. Fixing the `pytz` import cleared **both**
the SLA assertion failure and all the anomaly setup errors.

**Secondary bug found & fixed (was masking the above as a hang locally):**
`src/backend/integrations/k8s/client.py::list_pods()` called
`v1.list_pod_for_all_namespaces(watch=False)` with no request timeout. On a
machine with a `~/.kube/config` pointing at an unreachable cluster, the call
blocked forever, hanging the whole suite at `test_containers_endpoint` (the
docstring promises graceful `[]` — FM-11). Added `_request_timeout=3` so an
unreachable cluster fails fast and falls through to the intended graceful `[]`.
(On CI where the cluster refuses fast, this changes nothing.)

### The SLA assertion failure
Same `pytz` cause. `/api/sla` 500'd on naive DB timestamps.
**Fix:** replaced `import pytz; pytz.utc.localize(detected_at)` with the stdlib
`detected_at.replace(tzinfo=timezone.utc)` (`timezone` was already imported).

## Files changed
- `src/backend/sla/policy.py` — drop `pytz`, use stdlib `timezone.utc` (real bug fix).
- `src/backend/integrations/k8s/client.py` — add `_request_timeout=3` so an
  unreachable cluster fails fast instead of hanging (real bug fix, FM-11).
- `api/requirements.txt` — added `pytest>=8` and `pytest-asyncio` under a new `# Test` section.

No tests were weakened, skipped, xfailed, or deleted. No assertions changed.
All changes are within the write-set (tests/**, api/requirements.txt, src/backend/**/*.py);
`src/backend/logs/` untouched.

## requirements.txt diff
```
 python-dotenv>=1.0.0
 httpx>=0.27.0
+
+# Test
+pytest>=8
+pytest-asyncio
```
