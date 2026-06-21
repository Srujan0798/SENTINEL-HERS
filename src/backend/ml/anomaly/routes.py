"""Anomaly detection API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.backend.auth.dependencies import get_current_user_dependency
from src.backend.db import get_db

router = APIRouter(prefix="/api/ml", tags=["ml"])


class ScoreRequest(BaseModel):
    service: str
    metrics: list[float]


class TrainRequest(BaseModel):
    metrics_2d: list[list[float]]


@router.post("/score")
async def score_anomaly(
    body: ScoreRequest,
    current_user: dict = Depends(get_current_user_dependency),
):
    try:
        from src.backend.ml.anomaly.detector import score_metric_stream
        result = score_metric_stream(body.service, body.metrics)
        return {
            "service": body.service,
            "score": result.score,
            "is_anomaly": result.is_anomaly,
            "threshold": result.threshold,
        }
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"ML service unavailable: {exc}")


@router.post("/train")
async def retrain_model(
    body: TrainRequest,
    current_user: dict = Depends(get_current_user_dependency),
):
    if current_user.get("role") not in ("admin", "OWNER", "owner"):
        raise HTTPException(status_code=403, detail="Only owners can retrain the model")
    try:
        from src.backend.ml.anomaly.detector import retrain
        retrain(body.metrics_2d)
        return {"status": "retrained", "samples": len(body.metrics_2d)}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Retraining failed: {exc}")


@router.get("/anomalies")
async def list_anomalies(
    current_user: dict = Depends(get_current_user_dependency),
):
    """Demo endpoint: score a set of synthetic services and return any anomalies."""
    from src.backend.ml.anomaly.detector import score_metric_stream
    import random, time

    services = ["api-gateway", "auth-service", "db-worker", "cache-layer"]
    results = []
    for svc in services:
        # Mix of normal and anomalous values
        metrics = [random.uniform(0.2, 0.6) if svc != "db-worker" else random.uniform(0.9, 1.0)]
        score = score_metric_stream(svc, metrics)
        if score.is_anomaly:
            results.append({
                "service": svc,
                "score": score.score,
                "is_anomaly": True,
                "detected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            })
    return results
