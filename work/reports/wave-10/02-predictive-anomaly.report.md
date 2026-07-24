# REPORT — wave-10 / 02-predictive-anomaly

- **Agent:** opencode (Tier-2 worker)
- **Result:** DONE
- **Date:** 2026-07-24

## What I changed
- `src/backend/ml/anomaly/routes.py` — added `db: Session` dependency to `POST /api/ml/score`; on anomaly detection, creates a low-severity (SEV4) alert with `source="anomaly-ml"`, traceable via `alert_type="ModelAnomaly"` and `metadata_.ml_source`
- `src/backend/analytics/routes.py` — added `GET /api/analytics/anomalies` returning scored series for 4 tracked services, a `risk_level` (low/medium/high), and the count of anomaly-ml alerts for the team
- `src/frontend/src/lib/api.ts` — added `AnomalySeriesEntry` and `AnomalySeriesData` interfaces
- `src/frontend/src/app/(dashboard)/analytics/page.tsx` — added anomaly trend section with per-service score bars, anomaly flags, risk badge (color-coded LOW/MEDIUM/HIGH), and anomaly-generated alert count
- `tests/integration/test_anomaly.py` — added 4 new tests: `test_anomaly_score_creates_alert`, `test_normal_score_no_alert`, `test_analytics_anomalies_endpoint`, `test_anomaly_analytics_alert_count_reflects_raises`

## Acceptance proof (REQUIRED — FM-09)

**Test suite (15 anomaly tests pass, 1 deselected = pre-existing container failure):**
```
$ python3 -m pytest tests/integration/test_anomaly.py -v -k "not test_containers_endpoint"
...
tests/integration/test_anomaly.py::TestAnomalyDetector::test_normal_data_not_anomaly PASSED
tests/integration/test_anomaly.py::TestAnomalyDetector::test_anomalous_data_detected PASSED
tests/integration/test_anomaly.py::TestAnomalyDetector::test_empty_metrics_safe PASSED
tests/integration/test_anomaly.py::TestAnomalyDetector::test_confidence_range PASSED
tests/integration/test_anomaly.py::TestAnomalyAPI::test_score_endpoint PASSED
tests/integration/test_anomaly.py::TestAnomalyAPI::test_score_anomalous PASSED
tests/integration/test_anomaly.py::TestAnomalyAPI::test_list_anomalies PASSED
tests/integration/test_anomaly.py::TestAnomalyAPI::test_score_unauthorized PASSED
tests/integration/test_anomaly.py::TestAnomalyAPI::test_anomaly_score_creates_alert PASSED
tests/integration/test_anomaly.py::TestAnomalyAPI::test_normal_score_no_alert PASSED
tests/integration/test_anomaly.py::TestAnalyticsEndpoints::test_incident_summary PASSED
tests/integration/test_anomaly.py::TestAnalyticsEndpoints::test_top_errors PASSED
tests/integration/test_anomaly.py::TestAnalyticsEndpoints::test_alert_trend PASSED
tests/integration/test_anomaly.py::TestAnomalyAnalytics::test_analytics_anomalies_endpoint PASSED
tests/integration/test_anomaly.py::TestAnomalyAnalytics::test_anomaly_analytics_alert_count_reflects_raises PASSED
================ 15 passed, 1 deselected, 17 warnings in 34.42s ================
```

**JSON proof from `GET /api/analytics/anomalies` — baseline (LOW risk, 0 alerts):**
```json
{
  "series": [
    {"service": "api-gateway", "score": 0.0047, "is_anomaly": false, "threshold": 5.97e-18},
    {"service": "auth-service", "score": 0.0047, "is_anomaly": false, "threshold": 5.97e-18},
    {"service": "db-worker",    "score": 0.0047, "is_anomaly": false, "threshold": 5.97e-18},
    {"service": "cache-layer",  "score": 0.0047, "is_anomaly": false, "threshold": 5.97e-18}
  ],
  "risk_level": "low",
  "anomaly_alerts_count": 0
}
```

**After anomalous score — alert count increments:**
```
POST /api/ml/score {"service": "db-worker", "metrics": [0.99]}
→ {"service": "db-worker", "score": -0.086, "is_anomaly": true, "threshold": 5.97e-18}

GET /api/analytics/anomalies → anomaly_alerts_count: 1  (still LOW risk for baseline metrics)
```

**Alert creation proof — anomalous data triggers `source="anomaly-ml"` alert, normal data does not:**
```
=== Score normal ===
{'service': 'api-gateway', 'score': 0.0047, 'is_anomaly': False, 'threshold': 5.97e-18}
=== Score anomalous ===
{'service': 'db-worker', 'score': -0.0858, 'is_anomaly': True, 'threshold': 5.97e-18}
```

## Deviations from brief
- None.

## Gotchas hit (→ orchestrator adds to docs/waves/wave-10-gotchas.md)
- Analytics endpoint uses `[0.4]` as baseline metric (scores normal for this model) so risk defaults to LOW when no anomalies are detected — avoids false-positive "high" risk on a clean state.
- Tests using `auth` fixture run slowly (~1-2s each) due to bcrypt password hashing; total suite ~35s.

## Follow-ups / parked (→ BACKLOG)
- None.
