# TASK — wave-10 / 02-predictive-anomaly

> Self-contained brief. Brownie feature (rubric: AI/Automation 20% + System Design 25%).

## Goal (one sentence)
Elevate the existing anomaly-ML pipeline from a background score into a **visible predictive signal**:
surface anomaly trends + a "rising risk" indicator in the analytics UI and auto-raise a low-severity
alert when the model flags an outlier.

## Context
- Wave: 10. Depends on: wave-9 green.
- Existing: `src/backend/ml/` (IsolationForest + joblib), `tests/integration/test_anomaly.py`,
  `src/frontend/src/app/(dashboard)/analytics/page.tsx`, `src/backend/analytics/routes.py`.

## Write-set (FM-13)
- `src/backend/ml/` (prediction endpoint + threshold→alert hook)
- `src/backend/analytics/routes.py` (expose anomaly series — additive endpoint only)
- `src/frontend/src/app/(dashboard)/analytics/page.tsx` (anomaly trend chart + risk badge)
- `tests/integration/test_anomaly.py` (extend — prediction + alert-raise assertions)

## Forbid-set
- logs/incidents models internals, auth, deploy config

## Blast radius
r1. Auto-raised alerts must be low-severity + clearly model-generated (provenance), never auto-page.

## Steps
1. Add `GET /api/analytics/anomalies` returning the scored series + current risk level for the team.
2. On ingest/score, when score exceeds threshold, create a `source="anomaly-ml"` alert (traceable).
3. Analytics UI: render the anomaly trend + a risk badge; follow the `dataviz` skill for the chart.
4. Extend tests: feed known-anomalous data → assert an alert is raised and the series flags it.

## Acceptance (PROOF — FM-09)
- `python -m pytest tests/integration/test_anomaly.py -q` → pass. Paste it.
- Paste the JSON from `GET /api/analytics/anomalies` on seeded data showing a flagged point.

## Guardrails
- FM-09 real model output, no hardcoded "anomaly" · FM-11 fail loud if model artifact missing (don't silently return zeros).

## Report to
`work/reports/wave-10/02-predictive-anomaly.report.md`
