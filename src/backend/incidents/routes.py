from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.backend.auth.dependencies import get_current_user_dependency

from .database import get_db
from .enums import IncidentStatus, InvalidStateTransition, SeverityLevel
from pydantic import BaseModel

from .schemas import (
    AssignRequest,
    IncidentCreate,
    IncidentListResponse,
    IncidentResponse,
    IncidentUpdate,
    TimelineListResponse,
    TimelineEventResponse,
)
from .service import IncidentNotFound, IncidentService


class TimelineEventCreate(BaseModel):
    type: str
    description: str | None = None

router = APIRouter(prefix="/api/incidents", tags=["incidents"])


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(
    body: IncidentCreate,
    actor: str = Query("system"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    svc = IncidentService(db)
    result = svc.create_incident(
        team_id=current_user["team_id"],
        title=body.title,
        severity=body.severity,
        description=body.description,
        assigned_to=body.assigned_to,
        metadata=body.metadata,
        actor=actor,
    )
    return result


@router.get("", response_model=IncidentListResponse)
async def list_incidents(
    status_filter: Optional[IncidentStatus] = Query(None, alias="status"),
    severity: Optional[SeverityLevel] = None,
    assigned_to: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    svc = IncidentService(db)
    return svc.list_incidents(
        team_id=current_user["team_id"],
        status=status_filter,
        severity=severity,
        assigned_to=assigned_to,
        page=page,
        per_page=per_page,
    )


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    svc = IncidentService(db)
    try:
        return svc.get_incident(incident_id, current_user["team_id"])
    except IncidentNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")


@router.patch("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: UUID,
    body: IncidentUpdate,
    actor: str = Query("system"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    svc = IncidentService(db)
    updates = body.model_dump(exclude_unset=True)
    try:
        return svc.update_incident(incident_id, current_user["team_id"], updates, actor=actor)
    except IncidentNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    except InvalidStateTransition as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.post("/{incident_id}/assign", response_model=IncidentResponse)
async def assign_incident(
    incident_id: UUID,
    body: AssignRequest,
    actor: str = Query("system"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    svc = IncidentService(db)
    try:
        return svc.assign_incident(incident_id, current_user["team_id"], body.user_id, actor=actor)
    except IncidentNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")


@router.get("/{incident_id}/timeline", response_model=TimelineListResponse)
async def get_incident_timeline(
    incident_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    svc = IncidentService(db)
    try:
        events = svc.get_timeline(incident_id, current_user["team_id"])
        return {"data": events}
    except IncidentNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")


@router.post("/{incident_id}/timeline", status_code=status.HTTP_201_CREATED)
async def add_timeline_event(
    incident_id: UUID,
    body: TimelineEventCreate,
    actor: str = Query("system"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    svc = IncidentService(db)
    try:
        event = svc.add_timeline_event(
            incident_id=incident_id,
            team_id=current_user["team_id"],
            event_type=body.event_type,
            source=body.source,
            actor=actor,
            description=body.description,
            metadata=body.metadata,
        )
        return event
    except IncidentNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
