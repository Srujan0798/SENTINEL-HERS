"""AI endpoints — summary generation, root-cause analysis, conversational chat, and postmortem export."""
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.backend.auth.dependencies import get_current_user_dependency
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


def _get_incident_or_404(db: Session, incident_id: str, team_id: str | None = None) -> Incident:
    q = db.query(Incident).filter(Incident.id == incident_id)
    if team_id:
        q = q.filter(Incident.team_id == team_id)
    inc = q.first()
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
    current_user: dict = Depends(get_current_user_dependency),
):
    """Return cached summary or generate a new one via AI."""
    inc = _get_incident_or_404(db, incident_id, team_id=current_user["team_id"])

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
    current_user: dict = Depends(get_current_user_dependency),
):
    """Trigger root-cause analysis and return ranked hypotheses."""
    inc = _get_incident_or_404(db, incident_id, team_id=current_user["team_id"])

    logs = _fetch_logs(db, incident_id)

    # Fetch recent deployments for this team (best-effort)
    deployments: list[dict[str, Any]] = []
    try:
        from src.backend.integrations.github.models import Deployment

        deploy_rows = (
            db.query(Deployment)
            .filter(Deployment.team_id == current_user["team_id"])
            .order_by(Deployment.deployed_at.desc())
            .limit(10)
            .all()
        )
        deployments = [
            {"service": d.service, "version": d.version, "deployed_at": d.deployed_at.isoformat() if d.deployed_at else None}
            for d in deploy_rows
        ]
    except Exception:
        pass

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


class ChatRequest(BaseModel):
    question: str
    incident_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    citations: list[dict[str, Any]]
    confidence: float


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    body: ChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    """Team-scoped RAG chat over logs and incidents."""
    team_id = current_user["team_id"]

    incidents = []
    logs = []

    if body.incident_id:
        inc = db.query(Incident).filter(
            Incident.id == body.incident_id,
            Incident.team_id == team_id,
        ).first()
        if inc:
            incidents.append(_serialize_incident(inc))
            logs = _fetch_logs(db, body.incident_id)
    else:
        recent = db.query(Incident).filter(
            Incident.team_id == team_id,
        ).order_by(Incident.created_at.desc()).limit(10).all()
        incidents = [_serialize_incident(i) for i in recent]
        log_rows = db.query(LogEntryModel).filter(
            LogEntryModel.team_id == team_id,
        ).order_by(LogEntryModel.created_at.desc()).limit(50).all()
        logs = [
            {
                "id": str(r.id),
                "service": r.service,
                "level": r.level,
                "message": r.message,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in log_rows
        ]

    try:
        from src.backend.ai.chat.service import chat

        result = chat(
            team_id=team_id,
            user_message=body.question,
            history=[],
            incidents=incidents,
            logs=logs,
        )
        return ChatResponse(
            answer=result.answer,
            citations=[c.to_dict() for c in result.citations],
            confidence=result.confidence,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Chat unavailable: {exc}",
        )


class PostmortemResponse(BaseModel):
    incident_id: str
    content: str
    sections: dict[str, str]


@router.get("/postmortem/{incident_id}", response_model=PostmortemResponse)
async def get_postmortem(
    incident_id: str,
    format: str = Query("json", pattern="^(json|md)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    """Generate or retrieve a structured postmortem report for a resolved incident."""
    team_id = current_user["team_id"]
    inc = db.query(Incident).filter(
        Incident.id == incident_id,
        Incident.team_id == team_id,
    ).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident_dict = _serialize_incident(inc)
    timeline_events = _fetch_timeline(db, incident_id)
    root_causes = inc.ai_root_cause_ranking or []

    try:
        from src.backend.ai.postmortem.service import generate_postmortem

        report = generate_postmortem(
            incident=incident_dict,
            timeline_events=timeline_events,
            root_causes=root_causes,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Postmortem generation failed: {exc}",
        )

    if format == "md":
        return PlainTextResponse(
            content=report.content,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="postmortem-{incident_id[:8]}.md"',
            },
        )

    return PostmortemResponse(
        incident_id=report.incident_id,
        content=report.content,
        sections=report.sections,
    )


def _fetch_timeline(db: Session, incident_id: str) -> list[dict[str, Any]]:
    try:
        from src.backend.incidents.models import TimelineEvent
        rows = db.query(TimelineEvent).filter(
            TimelineEvent.incident_id == incident_id,
        ).order_by(TimelineEvent.ts.asc()).all()
        return [
            {
                "ts": e.ts.isoformat() if e.ts else None,
                "event_type": e.event_type,
                "actor": e.actor,
                "description": e.description,
            }
            for e in rows
        ]
    except Exception:
        return []
