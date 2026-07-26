"""Log search + alert read/resolve endpoints.

Mounted with NO prefix (see tests/integration/test_logs.py app fixture), so full
paths are declared on each route — matching the ingest router's convention.
Ingest itself (POST /api/ingest/logs, POST /api/ingest/alerts) lives in
src/backend/ingest/routes.py; this router owns the read/resolve side.
"""
import math
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.backend.auth.dependencies import get_current_user_dependency
from src.backend.rbac.dependencies import require_permission
from src.backend.logs.database import get_db
from src.backend.logs.models import (
    Alert,
    AlertModel,
    LogEntryModel,
    alert_from_orm,
)
from src.backend.shared.input_validator import InputValidator

router = APIRouter(tags=["logs"])


def _log_to_dict(r: LogEntryModel) -> dict[str, Any]:
    return {
        "id": str(r.id),
        "team_id": str(r.team_id),
        "incident_id": str(r.incident_id) if r.incident_id else None,
        "service": r.service,
        "level": r.level,
        "message": r.message,
        "metadata": r.metadata_ or {},
        "source_ip": r.source_ip,
        "indexed_at": r.indexed_at.isoformat() if r.indexed_at else None,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


@router.get("/api/logs/search")
async def search_logs(
    q: Optional[str] = Query(None),
    service: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    from_ts: Optional[datetime] = Query(None, alias="from"),
    to_ts: Optional[datetime] = Query(None, alias="to"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    team_id = current_user["team_id"]
    query = db.query(LogEntryModel).filter(LogEntryModel.team_id == team_id)

    # Validate and sanitize inputs
    if q:
        sanitized_q = InputValidator.sanitize_search_query(q)
        if sanitized_q:
            query = query.filter(LogEntryModel.message.ilike(f"%{sanitized_q}%"))
    
    if service:
        sanitized_service = InputValidator.validate_service_name(service)
        query = query.filter(LogEntryModel.service == sanitized_service)
    
    if level:
        sanitized_level = InputValidator.validate_log_level(level)
        query = query.filter(LogEntryModel.level == sanitized_level)
    
    if from_ts is not None:
        query = query.filter(LogEntryModel.created_at >= from_ts)
    if to_ts is not None:
        query = query.filter(LogEntryModel.created_at <= to_ts)

    total = query.count()
    rows = (
        query.order_by(LogEntryModel.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    total_pages = max(1, math.ceil(total / per_page)) if per_page else 1
    return {
        "data": [_log_to_dict(r) for r in rows],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
        },
    }


@router.get("/api/alerts", response_model=list[Alert])
async def list_alerts(
    is_resolved: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    team_id = current_user["team_id"]
    query = db.query(AlertModel).filter(AlertModel.team_id == team_id)
    if is_resolved is not None:
        query = query.filter(AlertModel.is_resolved == is_resolved)
    rows = query.order_by(AlertModel.created_at.desc()).all()
    return [alert_from_orm(r) for r in rows]


@router.post("/api/alerts/{alert_id}/resolve", response_model=Alert)
async def resolve_alert(
    alert_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
    _rbac=Depends(require_permission("logs:write")),
):
    team_id = current_user["team_id"]
    alert = (
        db.query(AlertModel)
        .filter(AlertModel.id == alert_id, AlertModel.team_id == team_id)
        .first()
    )
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )
    if alert.is_resolved:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Alert already resolved",
        )

    alert.is_resolved = True
    alert.resolved_at = datetime.now(timezone.utc)
    alert.resolved_by = current_user["id"]
    db.commit()
    db.refresh(alert)

    return alert_from_orm(alert)
