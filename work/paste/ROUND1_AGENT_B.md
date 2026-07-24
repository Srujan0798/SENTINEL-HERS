You are a Tier-2 worker on SENTINEL (METIS Hard — AI-native engineering ops platform).
Execute ONE self-contained task and STOP. Do not plan other waves. Do not push or deploy.

# LAW
1. Build ONLY what this brief asks. Write ONLY to the write-set. Never touch the forbid-set.
2. Do NOT redesign architecture or expand scope.
3. Fail loud: no bare `except: pass`, no silent fallback, no synthetic data to fake a pass.
4. Run acceptance commands. Paste REAL terminal output in your report. No proof = not done.
5. Write report to the exact path below using the report template structure at the end.
6. If blocked: report BLOCKED with one specific question — do not guess.
7. Sacred demo path must keep working: login → SEV1 → AI summary → assign/SLA → timeline → analytics.
8. Repo root: SENTINEL-HERS. Prefer mock AI (`AI_PROVIDER=mock`) for tests. Do not commit secrets.

# TASK — wave-10 / 02-predictive-anomaly

## Goal (one sentence)
Elevate the existing anomaly-ML pipeline from a background score into a **visible predictive signal**:
surface anomaly trends + a "rising risk" indicator in the analytics UI and auto-raise a low-severity
alert when the model flags an outlier.

## Context
- Wave: 10. Suite is green (~150 tests). Code already exists under `src/backend/ml/`.
- Existing: `src/backend/ml/` (IsolationForest + joblib), `tests/integration/test_anomaly.py`,
  `src/frontend/src/app/(dashboard)/analytics/page.tsx`, `src/backend/analytics/routes.py`.

## Write-set (ONLY these paths)
- `src/backend/ml/` (prediction endpoint + threshold→alert hook)
- `src/backend/analytics/routes.py` (expose anomaly series — additive endpoint only)
- `src/frontend/src/app/(dashboard)/analytics/page.tsx` (anomaly trend chart + risk badge)
- `tests/integration/test_anomaly.py` (extend — prediction + alert-raise assertions)
- `work/reports/wave-10/02-predictive-anomaly.report.md`

## Forbid-set (do NOT touch)
- logs/incidents model internals, auth/rbac, deploy config (`render.yaml`, `vercel.json`, `api/main.py`)
- any wave-10 task owned by another agent (chat, containers, voice, postmortem)

## Blast radius
r1. Auto-raised alerts must be low-severity + clearly model-generated (`source="anomaly-ml"`), never auto-page.

## Steps
1. Add `GET /api/analytics/anomalies` returning the scored series + current risk level for the team.
2. On ingest/score, when score exceeds threshold, create a `source="anomaly-ml"` alert (traceable).
3. Analytics UI: render the anomaly trend + a risk badge.
4. Extend tests: feed known-anomalous data → assert an alert is raised and the series flags it.

## Acceptance (PROOF required)
- `python -m pytest tests/integration/test_anomaly.py -q` → pass. Paste full output.
- Paste JSON from `GET /api/analytics/anomalies` on seeded/test data showing a flagged point.
- Optionally run `python -m pytest -q` and paste the summary line if time allows.

## Guardrails
- Real model output — no hardcoded "anomaly" labels.
- Fail loud if model artifact missing (don't silently return zeros).

## Report path
`work/reports/wave-10/02-predictive-anomaly.report.md`

### Report template
```
# REPORT — wave-10 / 02-predictive-anomaly
- **Agent:** <name>
- **Result:** DONE | PARTIAL | BLOCKED
- **Date:** <YYYY-MM-DD>
## What I changed
- ...
## Acceptance proof (REQUIRED)
```
$ command
output
```
## Deviations
## Gotchas
## Follow-ups
```

Then STOP.
