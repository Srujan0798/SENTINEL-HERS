"""Task management + SLA status endpoints."""
import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.backend.auth.dependencies import get_current_user_dependency
from src.backend.db import get_db
from src.backend.tasks.models import Task

router = APIRouter(tags=["tasks", "sla"])


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    assigned_to: Optional[str] = None
    due_at: Optional[datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    due_at: Optional[datetime] = None


@router.post("/api/incidents/{incident_id}/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(
    incident_id: UUID,
    body: TaskCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    team_id = current_user["team_id"]
    task = Task(
        id=str(uuid.uuid4()),
        team_id=team_id,
        incident_id=str(incident_id),
        title=body.title,
        description=body.description,
        priority=body.priority,
        assigned_to=body.assigned_to,
        due_at=body.due_at,
        created_by=current_user["id"],
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return _task_dict(task)


@router.get("/api/incidents/{incident_id}/tasks")
async def list_tasks(
    incident_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    team_id = current_user["team_id"]
    rows = db.query(Task).filter(
        Task.incident_id == str(incident_id),
        Task.team_id == team_id,
    ).order_by(Task.created_at.asc()).all()
    return {"data": [_task_dict(r) for r in rows]}


@router.patch("/api/tasks/{task_id}")
async def update_task(
    task_id: UUID,
    body: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    team_id = current_user["team_id"]
    task = db.query(Task).filter(Task.id == str(task_id), Task.team_id == team_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    for field, val in body.model_dump(exclude_none=True).items():
        setattr(task, field, val)
    task.updated_at = datetime.utcnow()
    if body.status == "completed" and not task.completed_at:
        task.completed_at = datetime.utcnow()

    db.commit()
    db.refresh(task)
    return _task_dict(task)


@router.get("/api/sla")
async def list_sla_status(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    from src.backend.incidents.models import Incident
    from src.backend.sla.policy import time_remaining_minutes, sla_minutes_for

    team_id = current_user["team_id"]
    open_statuses = ("detected", "triaging", "investigating", "mitigating")
    rows = db.query(Incident).filter(
        Incident.team_id == team_id,
        Incident.status.in_(open_statuses),
    ).all()

    result = []
    for inc in rows:
        if inc.detected_at:
            remaining = time_remaining_minutes(inc.detected_at, inc.severity)
            breached = remaining < 0
        else:
            remaining = sla_minutes_for(inc.severity)
            breached = False
        result.append({
            "incident_id": inc.id,
            "title": inc.title,
            "severity": inc.severity,
            "sla_minutes": sla_minutes_for(inc.severity),
            "remaining_minutes": round(remaining, 1),
            "breached": breached,
        })
    return result


def _task_dict(t: Task) -> dict:
    return {
        "id": t.id, "team_id": t.team_id, "incident_id": t.incident_id,
        "title": t.title, "description": t.description, "status": t.status,
        "priority": t.priority, "assigned_to": t.assigned_to,
        "due_at": str(t.due_at) if t.due_at else None,
        "completed_at": str(t.completed_at) if t.completed_at else None,
        "created_at": str(t.created_at),
    }
