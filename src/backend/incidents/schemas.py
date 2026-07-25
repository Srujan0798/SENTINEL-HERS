from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .enums import IncidentStatus, SeverityLevel


class IncidentCreate(BaseModel):
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    severity: SeverityLevel = SeverityLevel.SEV3
    assigned_to: Optional[UUID] = None
    metadata: dict[str, Any] = {}


class IncidentUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    severity: Optional[SeverityLevel] = None
    status: Optional[IncidentStatus] = None
    assigned_to: Optional[UUID] = None
    escalated_to: Optional[UUID] = None
    root_cause: Optional[str] = None


class AssignRequest(BaseModel):
    user_id: UUID


class EscalateRequest(BaseModel):
    user_id: UUID
    reason: Optional[str] = None


class IncidentResponse(BaseModel):
    id: UUID
    team_id: UUID
    title: str
    description: Optional[str]
    severity: SeverityLevel
    status: IncidentStatus
    assigned_to: Optional[UUID]
    escalated_to: Optional[UUID]
    detected_at: datetime
    triaged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]
    root_cause: Optional[str]
    ai_summary: Optional[str]
    ai_root_cause_ranking: Optional[list[dict[str, Any]]]
    metadata: dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TimelineEventCreate(BaseModel):
    event_type: str = Field(..., min_length=1, max_length=100)
    source: str = Field(default="api", max_length=255)
    description: Optional[str] = None
    metadata: dict[str, Any] = {}


class TimelineEventResponse(BaseModel):
    id: UUID
    incident_id: UUID
    event_type: str
    source: str
    actor: str
    ts: datetime
    payload_ref: Optional[str]
    description: Optional[str]
    metadata: dict[str, Any] = {}
    created_at: datetime

    class Config:
        from_attributes = True


class PaginationMeta(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int


class IncidentListResponse(BaseModel):
    data: list[IncidentResponse]
    pagination: PaginationMeta


class TimelineListResponse(BaseModel):
    data: list[TimelineEventResponse]
