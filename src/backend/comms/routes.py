"""Comms HTTP routes — channels + messages endpoints, nested under /api/incidents."""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.backend.auth.dependencies import get_current_user_dependency
from src.backend.db import get_db

from .schemas import (
    ChannelResponse,
    MessageCreate,
    MessageListResponse,
    MessageResponse,
    TeamMembersResponse,
    TeamMemberSummary,
)
from .service import (
    ChannelNotFound,
    CommsError,
    CommsService,
    IncidentNotFound,
)

router = APIRouter(prefix="/api/incidents", tags=["comms"])


@router.get("/{incident_id}/channel", response_model=ChannelResponse)
async def get_channel(
    incident_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    """Get (or auto-create) the channel for an incident."""
    team_id = current_user["team_id"]
    svc = CommsService(db)
    # Touch the incident first so we can surface a clean 404.
    from src.backend.incidents.models import Incident
    inc = db.query(Incident).filter(
        Incident.id == str(incident_id),
        Incident.team_id == team_id,
    ).first()
    if not inc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    try:
        channel = svc.get_or_create_channel_for_incident(
            incident_id=str(incident_id),
            team_id=str(team_id),
            incident_title=str(inc.title),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Channel init failed: {exc}")
    return svc.serialize_channel(channel)


@router.post(
    "/{incident_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def post_message(
    incident_id: UUID,
    body: MessageCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    """Post a message to the incident's channel. Fans out via realtime hub."""
    team_id = current_user["team_id"]
    user_id = current_user.get("id")
    # Best-effort display name (auth payload doesn't carry name; fall back to email).
    author_name = current_user.get("name") or current_user.get("email")

    svc = CommsService(db)
    try:
        result = svc.post_message(
            incident_id=str(incident_id),
            team_id=str(team_id),
            author_id=str(user_id) if user_id else None,
            author_name=author_name,
            body=body.body,
            author_type=body.author_type,
            metadata=body.metadata,
        )
    except ChannelNotFound:
        raise HTTPException(status_code=404, detail="Channel not found for incident")
    except CommsError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return result


@router.get("/{incident_id}/messages", response_model=MessageListResponse)
async def list_messages(
    incident_id: UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    """Paginated message history for an incident channel."""
    team_id = current_user["team_id"]
    svc = CommsService(db)
    try:
        channel = svc.get_channel_for_incident(str(incident_id), str(team_id))
    except ChannelNotFound:
        raise HTTPException(status_code=404, detail="Channel not found for incident")
    return svc.list_messages(channel_id=str(channel.id), page=page, per_page=per_page)


@router.get(
    "/{incident_id}/team-members",
    response_model=TeamMembersResponse,
    tags=["comms"],
)
async def list_team_members(
    incident_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    """Lightweight team-member list for @mention autocomplete in the UI."""
    team_id = current_user["team_id"]
    svc = CommsService(db)
    members = svc.list_channel_members(str(team_id))
    return {"data": members}
