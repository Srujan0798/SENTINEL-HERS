"""Pydantic schemas for comms endpoints."""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    body: str = Field(..., min_length=1, max_length=4000)
    author_type: str = Field("user", pattern="^(user|ai|system)$")
    metadata: dict[str, Any] = {}


class MentionInfo(BaseModel):
    user_id: str
    user_name: Optional[str] = None
    unresolved: bool = False


class MessageResponse(BaseModel):
    id: UUID
    team_id: UUID
    channel_id: UUID
    incident_id: UUID
    author_id: Optional[UUID]
    author_name: Optional[str]
    author_type: str
    body: str
    mentions: list[MentionInfo] = []
    metadata: dict[str, Any] = {}
    created_at: datetime
    edited_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChannelResponse(BaseModel):
    id: UUID
    team_id: UUID
    incident_id: UUID
    name: str
    topic: Optional[str]
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    member_count: int = 0
    message_count: int = 0

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    data: list[MessageResponse]
    pagination: "PaginationMeta"


class PaginationMeta(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int


class TeamMemberSummary(BaseModel):
    """Lightweight team member for @mention autocomplete."""
    id: UUID
    name: str
    email: str
    role: str


class TeamMembersResponse(BaseModel):
    data: list[TeamMemberSummary]


MessageListResponse.model_rebuild()
