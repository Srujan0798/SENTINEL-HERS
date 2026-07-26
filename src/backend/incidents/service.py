import math
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from .enums import IncidentStatus, InvalidStateTransition, SeverityLevel, validate_transition
from .models import Incident, TimelineEvent


def _serialize_incident(inc: Incident) -> dict[str, Any]:
    severity = inc.severity
    if isinstance(severity, SeverityLevel):
        severity = severity.value
    status = inc.status
    if isinstance(status, IncidentStatus):
        status = status.value
    return {
        "id": str(inc.id),
        "team_id": str(inc.team_id),
        "title": inc.title,
        "description": inc.description,
        "severity": severity,
        "status": status,
        "assigned_to": str(inc.assigned_to) if inc.assigned_to else None,
        "escalated_to": str(inc.escalated_to) if inc.escalated_to else None,
        "detected_at": inc.detected_at.isoformat() if inc.detected_at else None,
        "triaged_at": inc.triaged_at.isoformat() if hasattr(inc, "triaged_at") and inc.triaged_at else None,
        "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
        "closed_at": inc.closed_at.isoformat() if inc.closed_at else None,
        "root_cause": inc.root_cause,
        "ai_summary": inc.ai_summary,
        "ai_root_cause_ranking": inc.ai_root_cause_ranking,
        "metadata": inc.metadata_ if inc.metadata_ else {},
        "created_at": inc.created_at.isoformat() if inc.created_at else None,
        "updated_at": inc.updated_at.isoformat() if inc.updated_at else None,
    }


def _serialize_timeline_event(ev: TimelineEvent) -> dict[str, Any]:
    return {
        "id": str(ev.id),
        "incident_id": str(ev.incident_id),
        "event_type": ev.event_type,
        "source": ev.source,
        "actor": ev.actor,
        "ts": ev.ts.isoformat() if ev.ts else None,
        "payload_ref": ev.payload_ref,
        "description": ev.description,
        "metadata": ev.metadata_ if ev.metadata_ else {},
        "created_at": ev.created_at.isoformat() if ev.created_at else None,
    }


def _publish_event(team_id: str, event_type: str, payload: dict[str, Any]) -> None:
    try:
        from src.backend.realtime.hub import get_hub
        import asyncio
        hub = get_hub()
        asyncio.create_task(hub.publish(team_id, event_type, payload))
    except Exception:
        pass


def _try_dispatch_notifications(
    db: Session,
    channel: str,
    recipient: str,
    subject: str,
    message: str,
    incident_id: str | None = None,
) -> None:
    try:
        from src.backend.notifications.service import dispatch_notification
        dispatch_notification(db, channel, recipient, subject, message, incident_id)
    except Exception:
        pass


def _emit_timeline_event(
    db: Session,
    incident_id: str,
    event_type: str,
    source: str,
    actor: str,
    description: str,
    metadata: dict[str, Any] | None = None,
) -> TimelineEvent:
    ev = TimelineEvent(
        incident_id=incident_id,
        event_type=event_type,
        source=source,
        actor=actor,
        description=description,
        metadata_=metadata or {},
    )
    db.add(ev)
    db.flush()
    return ev


class IncidentService:
    def __init__(self, db: Session):
        self.db = db

    def create_incident(
        self,
        team_id: UUID,
        title: str,
        severity: SeverityLevel,
        description: str | None = None,
        assigned_to: UUID | None = None,
        metadata: dict[str, Any] | None = None,
        actor: str = "system",
    ) -> dict[str, Any]:
        inc = Incident(
            team_id=str(team_id),
            title=title,
            description=description,
            severity=severity.value,
            status=IncidentStatus.DETECTED.value,
            assigned_to=str(assigned_to) if assigned_to else None,
            metadata_=metadata or {},
        )
        self.db.add(inc)
        self.db.flush()

        _emit_timeline_event(
            db=self.db,
            incident_id=inc.id,
            event_type="incident.created",
            source="api",
            actor=actor,
            description=f"Incident created with severity {severity.value}",
        )
        _publish_event(str(team_id), "incident.create", {"incident_id": inc.id, "severity": severity.value, "status": IncidentStatus.DETECTED.value})
        _try_dispatch_notifications(self.db, "slack", "#incidents", f"[{severity.value}] {title}", description or "", inc.id)
        if severity in (SeverityLevel.SEV1, SeverityLevel.SEV2):
            _try_dispatch_notifications(self.db, "pagerduty", "", f"[{severity.value}] {title}", description or "", inc.id)
        self.db.commit()
        self.db.refresh(inc)
        return _serialize_incident(inc)

    def list_incidents(
        self,
        team_id: UUID,
        status: IncidentStatus | None = None,
        severity: SeverityLevel | None = None,
        assigned_to: UUID | None = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict[str, Any]:
        query = self.db.query(Incident).filter(Incident.team_id == str(team_id))

        if status is not None:
            query = query.filter(Incident.status == status.value)
        if severity is not None:
            query = query.filter(Incident.severity == severity.value)
        if assigned_to is not None:
            query = query.filter(Incident.assigned_to == str(assigned_to))

        total = query.count()
        total_pages = max(1, math.ceil(total / per_page))

        incidents = (
            query.order_by(Incident.detected_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return {
            "data": [_serialize_incident(inc) for inc in incidents],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
            },
        }

    def get_incident(self, incident_id: UUID, team_id: UUID) -> dict[str, Any]:
        inc = (
            self.db.query(Incident)
            .filter(Incident.id == str(incident_id), Incident.team_id == str(team_id))
            .first()
        )
        if not inc:
            raise IncidentNotFound(f"Incident {incident_id} not found")
        return _serialize_incident(inc)

    def update_incident(
        self,
        incident_id: UUID,
        team_id: UUID,
        updates: dict[str, Any],
        actor: str = "system",
    ) -> dict[str, Any]:
        inc = (
            self.db.query(Incident)
            .filter(Incident.id == str(incident_id), Incident.team_id == str(team_id))
            .first()
        )
        if not inc:
            raise IncidentNotFound(f"Incident {incident_id} not found")

        current_status = IncidentStatus(inc.status) if isinstance(inc.status, str) else inc.status

        new_status = updates.get("status")
        if new_status is not None:
            target_status = IncidentStatus(new_status) if isinstance(new_status, str) else new_status
            validate_transition(current_status, target_status)

            old_status = current_status
            inc.status = target_status.value

            now = datetime.now(timezone.utc)
            if target_status == IncidentStatus.TRIAGING:
                inc.triaged_at = now
            elif target_status == IncidentStatus.RESOLVED:
                inc.resolved_at = now
            elif target_status == IncidentStatus.CLOSED:
                inc.closed_at = now

            _emit_timeline_event(
                db=self.db,
                incident_id=inc.id,
                event_type="status.changed",
                source="api",
                actor=actor,
                description=f"Status changed from {old_status.value} to {target_status.value}",
                metadata={"old_status": old_status.value, "new_status": target_status.value},
            )
            _publish_event(str(team_id), "incident.update", {"incident_id": inc.id, "status": target_status.value, "old_status": old_status.value})

        for field in ("title", "description", "root_cause"):
            if field in updates and updates[field] is not None:
                setattr(inc, field, updates[field])

        if "severity" in updates and updates["severity"] is not None:
            sev = updates["severity"]
            inc.severity = sev.value if isinstance(sev, SeverityLevel) else sev

        if "assigned_to" in updates and updates["assigned_to"] is not None:
            inc.assigned_to = str(updates["assigned_to"])

        if "escalated_to" in updates and updates["escalated_to"] is not None:
            inc.escalated_to = str(updates["escalated_to"])

        if "metadata" in updates and updates["metadata"] is not None:
            inc.metadata_ = updates["metadata"]

        self.db.flush()
        self.db.commit()
        self.db.refresh(inc)
        return _serialize_incident(inc)

    def escalate_incident(
        self,
        incident_id: UUID,
        team_id: UUID,
        escalate_to: UUID,
        actor: str = "system",
        reason: str | None = None,
    ) -> dict[str, Any]:
        inc = (
            self.db.query(Incident)
            .filter(Incident.id == str(incident_id), Incident.team_id == str(team_id))
            .first()
        )
        if not inc:
            raise IncidentNotFound(f"Incident {incident_id} not found")
        inc.escalated_to = str(escalate_to)
        _emit_timeline_event(
            db=self.db,
            incident_id=inc.id,
            event_type="incident.escalated",
            source="api",
            actor=actor,
            description=f"Incident escalated to user {escalate_to}" + (f": {reason}" if reason else ""),
            metadata={"escalated_to": str(escalate_to), "reason": reason},
        )
        _publish_event(str(team_id), "incident.escalate", {"incident_id": inc.id, "escalated_to": str(escalate_to), "reason": reason})
        _try_dispatch_notifications(self.db, "slack", "#incidents", f"[ESCALATED] {inc.title}", reason or f"Escalated to {escalate_to}", inc.id)
        self.db.flush()
        self.db.commit()
        self.db.refresh(inc)
        return _serialize_incident(inc)

    def assign_incident(
        self,
        incident_id: UUID,
        team_id: UUID,
        user_id: UUID,
        actor: str = "system",
    ) -> dict[str, Any]:
        inc = (
            self.db.query(Incident)
            .filter(Incident.id == str(incident_id), Incident.team_id == str(team_id))
            .first()
        )
        if not inc:
            raise IncidentNotFound(f"Incident {incident_id} not found")

        inc.assigned_to = str(user_id)

        _emit_timeline_event(
            db=self.db,
            incident_id=inc.id,
            event_type="incident.assigned",
            source="api",
            actor=actor,
            description=f"Incident assigned to user {user_id}",
            metadata={"assigned_to": str(user_id)},
        )
        _publish_event(str(team_id), "incident.assign", {"incident_id": inc.id, "assigned_to": str(user_id)})
        self.db.flush()
        self.db.commit()
        self.db.refresh(inc)
        return _serialize_incident(inc)

    def add_timeline_event(
        self,
        incident_id: UUID,
        team_id: UUID,
        event_type: str,
        source: str = "api",
        actor: str = "system",
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        inc = (
            self.db.query(Incident)
            .filter(Incident.id == str(incident_id), Incident.team_id == str(team_id))
            .first()
        )
        if not inc:
            raise IncidentNotFound(f"Incident {incident_id} not found")

        ev = _emit_timeline_event(
            db=self.db,
            incident_id=inc.id,
            event_type=event_type,
            source=source,
            actor=actor,
            description=description,
            metadata=metadata,
        )
        self.db.commit()
        self.db.refresh(ev)
        return _serialize_timeline_event(ev)

    def get_timeline(
        self,
        incident_id: UUID,
        team_id: UUID,
    ) -> list[dict[str, Any]]:
        inc = (
            self.db.query(Incident)
            .filter(Incident.id == str(incident_id), Incident.team_id == str(team_id))
            .first()
        )
        if not inc:
            raise IncidentNotFound(f"Incident {incident_id} not found")

        events = (
            self.db.query(TimelineEvent)
            .filter(TimelineEvent.incident_id == str(incident_id))
            .order_by(TimelineEvent.ts.asc())
            .all()
        )
        return [_serialize_timeline_event(ev) for ev in events]


class IncidentNotFound(Exception):
    pass
