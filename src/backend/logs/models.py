"""ORM models, Pydantic schemas, and enums for the logs/alerts domain.

Field contract is reverse-engineered from src/backend/ingest/routes.py,
src/backend/analytics/routes.py, and src/backend/ai/routes.py — the columns and
schema fields those modules read/write must exist here EXACTLY. Do not drift.
"""
import enum
import uuid
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Index,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.types import TypeDecorator

# Reuse the incident severity enum so alert/incident severities never drift apart.
from src.backend.incidents.enums import SeverityLevel  # noqa: F401 (re-exported)

from .database import Base


class LogLevel(str, enum.Enum):
    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error"
    FATAL = "fatal"


class _UuidStr(TypeDecorator):
    """Store UUIDs as 36-char strings (SQLite-friendly), hand back UUID objects.

    Binds cleanly whether given a UUID or a str (auth hands us str team_id/user
    ids; ingest hands us uuid.uuid4() objects).
    """

    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return str(value) if value is not None else None

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return UUID(value)


# --------------------------------------------------------------------------- #
# ORM models
# --------------------------------------------------------------------------- #
class LogEntryModel(Base):
    __tablename__ = "log_entries"

    id = Column(_UuidStr, primary_key=True, default=uuid.uuid4)
    team_id = Column(_UuidStr, nullable=False, index=True)
    incident_id = Column(_UuidStr, nullable=True, index=True)
    service = Column(String(255), nullable=False, index=True)
    level = Column(String(20), nullable=False, index=True)
    message = Column(Text, nullable=False)
    metadata_ = Column("metadata", JSON, server_default=text("'{}'"))
    source_ip = Column(String(64), nullable=True)
    indexed_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)

    # implicit_returning=False disables SQLAlchemy's insertmanyvalues RETURNING
    # sentinel, which otherwise KeyErrors when a _UuidStr PK is bulk-inserted with
    # explicit ids (result -> UUID) that differ from the original str params.
    __table_args__ = (
        Index("ix_log_entries_team_created", "team_id", "created_at"),
        Index("ix_log_entries_team_service_level", "team_id", "service", "level"),
        {"implicit_returning": False},
    )


class AlertModel(Base):
    __tablename__ = "alerts"

    id = Column(_UuidStr, primary_key=True, default=uuid.uuid4)
    team_id = Column(_UuidStr, nullable=False, index=True)
    incident_id = Column(_UuidStr, nullable=True, index=True)
    source = Column(String(255), nullable=False)
    alert_type = Column(String(255), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(10), nullable=False, default=SeverityLevel.SEV3.value)
    is_resolved = Column(Boolean, nullable=False, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(_UuidStr, nullable=True)
    metadata_ = Column("metadata", JSON, server_default=text("'{}'"))
    fired_at = Column(DateTime, nullable=False, server_default=func.now())
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)

    __table_args__ = ({"implicit_returning": False},)


# --------------------------------------------------------------------------- #
# Pydantic schemas
# --------------------------------------------------------------------------- #
class LogIngest(BaseModel):
    """One inbound log entry (bulk-wrapped by ingest.BulkLogIngestRequest)."""

    service: str
    level: LogLevel
    message: str
    metadata: dict[str, Any] = {}
    source_ip: Optional[str] = None


class LogEntry(BaseModel):
    id: UUID
    team_id: UUID
    incident_id: Optional[UUID] = None
    service: str
    level: LogLevel
    message: str
    metadata: dict[str, Any] = {}
    source_ip: Optional[str] = None
    indexed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AlertCreate(BaseModel):
    source: str
    alert_type: str
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    severity: SeverityLevel = SeverityLevel.SEV3
    metadata: dict[str, Any] = {}


class Alert(BaseModel):
    id: UUID
    team_id: UUID
    incident_id: Optional[UUID] = None
    source: str
    alert_type: str
    title: str
    description: Optional[str] = None
    severity: SeverityLevel
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[UUID] = None
    metadata: dict[str, Any] = {}
    fired_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


def alert_from_orm(r: AlertModel) -> Alert:
    """Map an AlertModel row to the Alert schema (metadata_ -> metadata)."""
    return Alert(
        id=r.id,
        team_id=r.team_id,
        incident_id=r.incident_id,
        source=r.source,
        alert_type=r.alert_type,
        title=r.title,
        description=r.description,
        severity=r.severity,
        is_resolved=r.is_resolved,
        resolved_at=r.resolved_at,
        resolved_by=r.resolved_by,
        metadata=r.metadata_ or {},
        fired_at=r.fired_at,
        created_at=r.created_at,
    )
