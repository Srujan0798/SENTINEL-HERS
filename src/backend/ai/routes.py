"""AI endpoints — summary generation + root-cause analysis for incidents."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.backend.db import get_db
from src.backend.incidents.models import Incident
from src.backend.logs.models import LogEntryModel, AlertModel

router = APIRouter(prefix="/api/ai", tags=["ai"])


class RootCauseResponse(BaseModel):
    hypothesis: str
    confidence: float
    supporting_evidence: list[str]
    suggested_action: str


class SummaryResponse(BaseModel):
    incident_id: str
    summary: str


class RootCauseListResponse(BaseModel):
    incident_id: str
    root_causes: list[RootCauseResponse]


def _get_incident_or_404(db: Session, incident_id: str) -> Incident:
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    return inc


def _fetch_logs(db: Session, incident_id: str) -> list[dict[str, Any]]:
    rows = (
        db.query(LogEntryModel)
        .filter(LogEntryModel.incident_id == incident_id)
        .order_by(LogEntryModel.created_at.desc())
        .limit(100)
        .all()
    )
    return [
        {
            "id": str(r.id),
            "service": r.service,
            "level": r.level,
            "message": r.message,
            "source_ip": r.source_ip,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


def _fetch_alerts(db: Session, incident_id: str) -> list[dict[str, Any]]:
    rows = (
        db.query(AlertModel)
        .filter(AlertModel.incident_id == incident_id)
        .order_by(AlertModel.fired_at.desc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": str(r.id),
            "source": r.source,
            "alert_type": r.alert_type,
            "title": r.title,
            "description": r.description,
            "severity": r.severity,
            "fired_at": r.fired_at.isoformat() if r.fired_at else None,
        }
        for r in rows
    ]


def _serialize_incident(inc: Incident) -> dict[str, Any]:
    return {
        "id": str(inc.id),
        "team_id": str(inc.team_id),
        "title": inc.title,
        "description": inc.description,
        "severity": inc.severity,
        "status": inc.status,
        "detected_at": inc.detected_at.isoformat() if inc.detected_at else None,
    }


@router.get(
    "/incidents/{incident_id}/summary",
    response_model=SummaryResponse,
)
async def get_incident_summary(
    incident_id: str,
    db: Session = Depends(get_db),
):
    """Return cached summary or generate a new one via AI."""
    inc = _get_incident_or_404(db, incident_id)

    # If already cached on the incident, return it
    if inc.ai_summary:
        return SummaryResponse(incident_id=str(inc.id), summary=inc.ai_summary)

    logs = _fetch_logs(db, incident_id)
    alerts = _fetch_alerts(db, incident_id)
    incident_dict = _serialize_incident(inc)

    try:
        from src.backend.ai.summary.service import generate_incident_summary

        summary = generate_incident_summary(incident_dict, logs, alerts)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "ai_unavailable", "fallback": None},
        )

    # Persist the summary on the incident
    inc.ai_summary = summary
    db.commit()
    db.refresh(inc)

    return SummaryResponse(incident_id=str(inc.id), summary=summary)


@router.post(
    "/incidents/{incident_id}/root-causes",
    response_model=RootCauseListResponse,
)
async def get_incident_root_causes(
    incident_id: str,
    db: Session = Depends(get_db),
):
    """Trigger root-cause analysis and return ranked hypotheses."""
    inc = _get_incident_or_404(db, incident_id)

    logs = _fetch_logs(db, incident_id)

    # Fetch recent deployments for this team (best-effort)
    deployments: list[dict[str, Any]] = []
    try:
        from src.backend.logs.models import LogEntryModel as _LEM

        services = {
            r[0]
            for r in db.query(_LEM.service)
            .filter(_LEM.incident_id == incident_id)
            .distinct()
            .all()
        }
    except Exception:
        services = set()

    incident_dict = _serialize_incident(inc)

    try:
        from src.backend.ai.rootcause.service import suggest_root_causes

        suggestions = suggest_root_causes(incident_dict, logs, deployments)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "ai_unavailable", "fallback": None},
        )

    result = RootCauseListResponse(
        incident_id=str(inc.id),
        root_causes=[RootCauseResponse(**s.to_dict()) for s in suggestions],
    )

    # Persist ranking on the incident
    inc.ai_root_cause_ranking = [s.to_dict() for s in suggestions]
    db.commit()

    return result
