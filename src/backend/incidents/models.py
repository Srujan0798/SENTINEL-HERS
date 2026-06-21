import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, func, JSON, text
from sqlalchemy.orm import relationship

from .database import Base
from .enums import IncidentStatus, SeverityLevel


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    team_id = Column(String(36), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(10), nullable=False, default=SeverityLevel.SEV3.value)
    status = Column(String(20), nullable=False, default=IncidentStatus.DETECTED.value)
    assigned_to = Column(String(36), nullable=True)
    escalated_to = Column(String(36), nullable=True)
    detected_at = Column(DateTime, nullable=False, server_default=func.now())
    triaged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    root_cause = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    ai_root_cause_ranking = Column(JSON, nullable=True)
    metadata_ = Column("metadata", JSON, server_default=text("'{}'"))
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    timeline_events = relationship(
        "TimelineEvent", back_populates="incident", cascade="all, delete-orphan"
    )


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id = Column(
        String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type = Column(String(100), nullable=False, index=True)
    source = Column(String(255), nullable=False)
    actor = Column(String(255), nullable=False)
    ts = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    payload_ref = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, server_default=text("'{}'"))
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    incident = relationship("Incident", back_populates="timeline_events")
