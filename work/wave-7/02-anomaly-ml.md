# TASK — wave-7 / 02-anomaly-ml

## Goal
ML-based predictive anomaly detection on metric streams. Flags injected anomaly in eval (bonus criterion).

## Context
- Wave: 7. Reads service health metrics + log volume. Model stored in `models/anomaly/`.
- Use lightweight approach: Isolation Forest or Z-score on rolling window (no GPU needed).

## Write-set (ONLY these)
- src/backend/ml/anomaly/
- models/anomaly/

## Forbid-set
- src/backend/analytics/ (01 owns), src/backend/integrations/ (03 owns)

## Blast radius
r1.

## Steps
1. `anomaly/detector.py`: `AnomalyDetector` using scikit-learn IsolationForest trained on synthetic baseline metrics.
2. `anomaly/service.py`: 
   - `score_metric_stream(service_name, metrics: list[float]) -> AnomalyScore` — returns `{score: float, is_anomaly: bool, threshold: float}`.
   - Background task: every 2min, score all active services; if anomaly detected → emit `anomaly.detected` realtime event + create SEV3 alert automatically.
3. `POST /api/ml/train` — retrain model on last 7d of metrics (owner only).
4. `GET /api/ml/anomalies` — list recent anomaly scores with service + ts.
5. Save trained model to `models/anomaly/model.pkl`.
6. Seed with synthetic baseline + one injected anomaly to prove detection works.

## Acceptance (PROOF — FM-09)
```
pytest tests/integration/test_anomaly.py -v
# Expected: injected anomaly scored is_anomaly=true; normal data scored is_anomaly=false
```

## Report to
`work/reports/wave-7/02-anomaly-ml.report.md`
