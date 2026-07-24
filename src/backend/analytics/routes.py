"""Analytics dashboard endpoints — incident trends, MTTR, top error services."""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from src.backend.auth.dependencies import get_current_user_dependency
from src.backend.db import get_db

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/incidents/summary")
async def incident_summary(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    from src.backend.incidents.models import Incident
    team_id = current_user["team_id"]
    since = datetime.now(timezone.utc) - timedelta(days=days)

    rows = db.query(Incident).filter(
        Incident.team_id == team_id,
        Incident.created_at >= since,
    ).all()

    total = len(rows)
    by_severity: dict[str, int] = {}
    by_status: dict[str, int] = {}
    resolved = [r for r in rows if r.resolved_at and r.detected_at]
    mttr_minutes = 0.0
    if resolved:
        durations = []
        for r in resolved:
            det = r.detected_at
            res = r.resolved_at
            if det and res:
                durations.append((res - det).total_seconds() / 60)
        if durations:
            mttr_minutes = sum(durations) / len(durations)

    for r in rows:
        by_severity[r.severity] = by_severity.get(r.severity, 0) + 1
        by_status[r.status] = by_status.get(r.status, 0) + 1

    open_count = total - len(resolved)
    return {
        "period_days": days,
        "total_incidents": total,
        "open_incidents": open_count,
        "resolved_incidents": len(resolved),
        "by_severity": by_severity,
        "by_status": by_status,
        "mttr_minutes": round(mttr_minutes, 1),
        "resolved_count": len(resolved),  # alias for older clients
    }


@router.get("/logs/top-errors")
async def top_error_services(
    days: int = Query(1, ge=1, le=30),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    from src.backend.logs.models import LogEntryModel
    team_id = current_user["team_id"]
    since = datetime.now(timezone.utc) - timedelta(days=days)

    rows = db.query(
        LogEntryModel.service,
        func.count(LogEntryModel.id).label("error_count"),
    ).filter(
        LogEntryModel.team_id == team_id,
        LogEntryModel.level.in_(["error", "fatal"]),
        LogEntryModel.created_at >= since,
    ).group_by(LogEntryModel.service).order_by(
        func.count(LogEntryModel.id).desc()
    ).limit(limit).all()

    return [{"service": r.service, "error_count": r.error_count} for r in rows]


@router.get("/alerts/trend")
async def alert_trend(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    from src.backend.logs.models import AlertModel
    team_id = current_user["team_id"]
    since = datetime.now(timezone.utc) - timedelta(days=days)

    rows = db.query(AlertModel).filter(
        AlertModel.team_id == team_id,
        AlertModel.created_at >= since,
    ).order_by(AlertModel.created_at.asc()).all()

    total = len(rows)
    resolved = sum(1 for r in rows if r.is_resolved)
    by_severity: dict[str, int] = {}
    for r in rows:
        sev = r.severity if isinstance(r.severity, str) else str(r.severity)
        by_severity[sev] = by_severity.get(sev, 0) + 1

    return {
        "period_days": days,
        "total_alerts": total,
        "resolved_alerts": resolved,
        "open_alerts": total - resolved,
        "by_severity": by_severity,
    }


@router.get("/anomalies")
async def anomaly_series(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    """Return scored anomaly series for tracked services plus overall risk level."""
    from src.backend.ml.anomaly.detector import score_metric_stream
    from src.backend.logs.models import AlertModel

    services = ["api-gateway", "auth-service", "db-worker", "cache-layer"]
    series = []
    anomalous_count = 0

    for svc in services:
        metrics = [0.4]
        try:
            result = score_metric_stream(svc, metrics)
        except Exception:
            raise HTTPException(status_code=503, detail="Anomaly model unavailable")
        entry = {
            "service": svc,
            "score": result.score,
            "is_anomaly": result.is_anomaly,
            "threshold": result.threshold,
        }
        series.append(entry)
        if result.is_anomaly:
            anomalous_count += 1

    team_id = current_user["team_id"]
    alert_count = db.query(AlertModel).filter(
        AlertModel.team_id == team_id,
        AlertModel.source == "anomaly-ml",
    ).count()

    if anomalous_count >= 2:
        risk_level = "high"
    elif anomalous_count == 1:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "series": series,
        "risk_level": risk_level,
        "anomaly_alerts_count": alert_count,
    }
