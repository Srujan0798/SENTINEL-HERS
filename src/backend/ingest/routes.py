import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from src.backend.auth.dependencies import get_current_user_dependency
from src.backend.logs.database import get_db
from src.backend.logs.models import (
    Alert,
    AlertCreate,
    AlertModel,
    LogEntry,
    LogEntryModel,
    LogIngest,
    LogLevel,
    SeverityLevel,
)
from src.backend.realtime.hub import get_hub

router = APIRouter(tags=["ingest"])

def _alert_from_orm(r: AlertModel) -> Alert:
    return Alert(
        id=r.id, team_id=r.team_id, incident_id=r.incident_id,
        source=r.source, alert_type=r.alert_type, title=r.title,
        description=r.description, severity=r.severity,
        is_resolved=r.is_resolved, resolved_at=r.resolved_at,
        resolved_by=r.resolved_by, metadata=r.metadata_ or {},
        fired_at=r.fired_at, created_at=r.created_at,
    )



class BulkLogIngestRequest(BaseModel):
    entries: list[LogIngest] = Field(..., min_length=1, max_length=1000)

    @field_validator("entries")
    @classmethod
    def validate_entries(cls, v: list[LogIngest]) -> list[LogIngest]:
        for i, entry in enumerate(v):
            if not entry.service or not entry.service.strip():
                raise ValueError(f"entries[{i}].service: must not be empty")
            if not entry.message or not entry.message.strip():
                raise ValueError(f"entries[{i}].message: must not be empty")
        return v


class BulkLogIngestResponse(BaseModel):
    accepted: int
    entries: list[LogEntry]


@router.post("/api/ingest/logs", response_model=BulkLogIngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_logs(
    body: BulkLogIngestRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    team_id = current_user["team_id"]
    now = datetime.now(timezone.utc)
    created: list[LogEntryModel] = []

    for item in body.entries:
        entry = LogEntryModel(
            id=uuid.uuid4(),
            team_id=team_id,
            service=item.service,
            level=item.level,
            message=item.message,
            metadata_=item.metadata or {},
            source_ip=item.source_ip,
            indexed_at=now,
            created_at=now,
        )
        db.add(entry)
        created.append(entry)

    db.commit()
    for e in created:
        db.refresh(e)

    def _orm_to_log_entry(e: LogEntryModel) -> LogEntry:
        return LogEntry(
            id=e.id, team_id=e.team_id, incident_id=e.incident_id,
            service=e.service, level=e.level, message=e.message,
            metadata=e.metadata_ or {}, source_ip=e.source_ip,
            indexed_at=e.indexed_at, created_at=e.created_at,
        )

    return BulkLogIngestResponse(
        accepted=len(created),
        entries=[_orm_to_log_entry(e) for e in created],
    )


@router.post("/api/ingest/alerts", response_model=Alert, status_code=status.HTTP_201_CREATED)
async def create_alert(
    body: AlertCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    team_id = current_user["team_id"]
    now = datetime.now(timezone.utc)
    alert_id = uuid.uuid4()

    alert = AlertModel(
        id=alert_id,
        team_id=team_id,
        source=body.source,
        alert_type=body.alert_type,
        title=body.title,
        description=body.description,
        severity=body.severity,
        metadata_=body.metadata or {},
        fired_at=now,
        created_at=now,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    hub = get_hub()
    await hub.publish(
        team_id=str(team_id),
        event_type="alert.created",
        payload={
            "id": str(alert.id),
            "source": alert.source,
            "alert_type": alert.alert_type,
            "title": alert.title,
            "severity": alert.severity,
            "fired_at": alert.fired_at.isoformat(),
        },
    )

    return _alert_from_orm(alert)
