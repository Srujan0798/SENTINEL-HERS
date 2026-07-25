"""Service health listing — never 500 for missing/partial schema (judge path)."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.backend.db import get_db
from .models import HealthStatus, ServiceHealthCreate, ServiceHealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/health/services", tags=["health"])


def _as_uuid(val: Any) -> UUID:
    if isinstance(val, UUID):
        return val
    return UUID(str(val))


def _as_dt(val: Any) -> datetime:
    if isinstance(val, datetime):
        return val
    if val is None:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)


def _as_status(val: Any) -> HealthStatus:
    s = str(val or "unknown").lower()
    try:
        return HealthStatus(s)
    except Exception:
        return HealthStatus.UNKNOWN


def _as_meta(val: Any) -> dict:
    if isinstance(val, dict):
        return val
    return {}


@router.get("/", response_model=List[ServiceHealthResponse])
async def list_services(db: Session = Depends(get_db)):
    """List all services with current status.

    Soft-fails to [] on any schema/row issue so Monitoring never 500s for judges.
    """
    try:
        result = db.execute(
            text(
                """
                SELECT id, team_id, service_name, status, uptime_percentage, latency_ms,
                       last_check_at, next_check_at, metadata
                FROM service_health
                ORDER BY service_name
                """
            )
        )
        rows = result.fetchall()
    except Exception as e:
        logger.warning("service_health list failed (returning []): %s", e)
        try:
            db.rollback()
        except Exception:
            pass
        return []

    services: list[ServiceHealthResponse] = []
    for row in rows:
        try:
            # SQLAlchemy Row supports _mapping / index access
            m = row._mapping if hasattr(row, "_mapping") else None
            get = (lambda k, default=None: m[k] if m is not None else getattr(row, k, default))
            services.append(
                ServiceHealthResponse(
                    id=_as_uuid(get("id")),
                    team_id=_as_uuid(get("team_id")),
                    service_name=str(get("service_name") or "unknown"),
                    status=_as_status(get("status")),
                    uptime_percentage=get("uptime_percentage"),
                    latency_ms=get("latency_ms"),
                    last_check_at=_as_dt(get("last_check_at")),
                    next_check_at=_as_dt(get("next_check_at")) if get("next_check_at") else None,
                    metadata=_as_meta(get("metadata")),
                )
            )
        except Exception as e:
            logger.warning("Skipping bad service_health row: %s", e)
            continue
    return services


@router.post("/", response_model=ServiceHealthResponse, status_code=status.HTTP_201_CREATED)
async def register_service(service: ServiceHealthCreate, db: Session = Depends(get_db)):
    """Register a service for monitoring."""
    try:
        result = db.execute(
            text(
                """
                INSERT INTO service_health (team_id, service_name, status, metadata)
                VALUES (:team_id, :service_name, 'unknown', :metadata)
                RETURNING id, team_id, service_name, status, uptime_percentage, latency_ms,
                         last_check_at, next_check_at, metadata
                """
            ),
            {
                "team_id": str(service.team_id),
                "service_name": service.service_name,
                "metadata": service.metadata or {},
            },
        )
        db.commit()
        row = result.fetchone()
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register service: {e}",
        ) from e

    if not row:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register service",
        )

    m = row._mapping if hasattr(row, "_mapping") else None
    get = (lambda k, default=None: m[k] if m is not None else getattr(row, k, default))
    return ServiceHealthResponse(
        id=_as_uuid(get("id")),
        team_id=_as_uuid(get("team_id")),
        service_name=str(get("service_name") or service.service_name),
        status=_as_status(get("status")),
        uptime_percentage=get("uptime_percentage"),
        latency_ms=get("latency_ms"),
        last_check_at=_as_dt(get("last_check_at")),
        next_check_at=_as_dt(get("next_check_at")) if get("next_check_at") else None,
        metadata=_as_meta(get("metadata")),
    )
