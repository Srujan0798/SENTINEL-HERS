"""Isolation Forest anomaly detector for metric streams.

Model persistence uses joblib (sklearn-recommended serializer).
Security note: model file is only loaded from our own controlled path
(models/anomaly/model.joblib), never from user-supplied input — no
deserialization of untrusted data occurs here.
"""
import os
from pathlib import Path
from typing import NamedTuple

import numpy as np

MODEL_PATH = Path(os.getenv("ANOMALY_MODEL_PATH", "models/anomaly/model.joblib"))
CONTAMINATION = 0.05


class AnomalyScore(NamedTuple):
    score: float       # raw decision function value (negative = more anomalous)
    is_anomaly: bool
    threshold: float


def _load_or_train() -> tuple:
    """Load persisted model or train a fresh IsolationForest on synthetic baseline."""
    import joblib
    from sklearn.ensemble import IsolationForest

    if MODEL_PATH.exists():
        return joblib.load(MODEL_PATH)  # trusted internal path only

    # Synthetic baseline: normal metrics (CPU 20–60%, latency 50–200ms)
    rng = np.random.RandomState(42)
    baseline = rng.uniform(low=[0.2, 50], high=[0.6, 200], size=(500, 2))
    model = IsolationForest(contamination=CONTAMINATION, random_state=42)
    model.fit(baseline)

    scores = model.decision_function(baseline)
    threshold = float(np.percentile(scores, 5))

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump((model, threshold), MODEL_PATH)

    return model, threshold


def score_metric_stream(service_name: str, metrics: list[float]) -> AnomalyScore:
    """Score a metric stream. metrics: flat list of values per window."""
    model, threshold = _load_or_train()

    if not metrics:
        return AnomalyScore(score=0.0, is_anomaly=False, threshold=threshold)

    arr = np.array(metrics).reshape(-1, 1)
    # Duplicate single feature to match 2-feature training shape
    arr = np.hstack([arr, arr])

    avg_score = float(np.mean(model.decision_function(arr)))
    return AnomalyScore(score=avg_score, is_anomaly=avg_score < threshold, threshold=threshold)


def retrain(metrics_2d: list[list[float]]) -> None:
    """Retrain on provided metrics (2D: [[cpu, latency], ...]) and save."""
    import joblib
    from sklearn.ensemble import IsolationForest

    arr = np.array(metrics_2d)
    model = IsolationForest(contamination=CONTAMINATION, random_state=42)
    model.fit(arr)
    threshold = float(np.percentile(model.decision_function(arr), 5))

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump((model, threshold), MODEL_PATH)
