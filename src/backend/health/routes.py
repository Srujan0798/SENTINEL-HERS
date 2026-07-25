import os
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.backend.db import get_db
from .models import ServiceHealth, ServiceHealthCreate, ServiceHealthResponse

router = APIRouter(prefix="/api/health/services", tags=["health"])


@router.get("/", response_model=List[ServiceHealthResponse])
async def list_services(db: Session = Depends(get_db)):
    """List all services with current status.

    Soft-fails to [] when the table is missing (fresh DBs / partial migrations)
    so Monitoring never 500s for judges.
    """
    try:
        result = db.execute(text("""
            SELECT id, team_id, service_name, status, uptime_percentage, latency_ms,
                   last_check_at, next_check_at, metadata, created_at, updated_at
            FROM service_health
            ORDER BY service_name
        """))
    except Exception:
        db.rollback()
        return []

    services = []
    for row in result.fetchall():
        services.append(ServiceHealthResponse(
            id=row.id,
            team_id=row.team_id,
            service_name=row.service_name,
            status=row.status,
            uptime_percentage=row.uptime_percentage,
            latency_ms=row.latency_ms,
            last_check_at=row.last_check_at,
            next_check_at=row.next_check_at,
            metadata=row.metadata or {},
        ))

    return services


@router.post("/", response_model=ServiceHealthResponse, status_code=status.HTTP_201_CREATED)
async def register_service(service: ServiceHealthCreate, db: Session = Depends(get_db)):
    """Register a service for monitoring"""
    result = db.execute(text("""
        INSERT INTO service_health (team_id, service_name, status, metadata)
        VALUES (:team_id, :service_name, 'unknown', :metadata)
        RETURNING id, team_id, service_name, status, uptime_percentage, latency_ms,
                 last_check_at, next_check_at, metadata, created_at, updated_at
    """), {
        "team_id": service.team_id,
        "service_name": service.service_name,
        "metadata": service.metadata
    })

    row = result.fetchone()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register service"
        )

    return ServiceHealthResponse(
        id=row.id,
        team_id=row.team_id,
        service_name=row.service_name,
        status=row.status,
        uptime_percentage=row.uptime_percentage,
        latency_ms=row.latency_ms,
        last_check_at=row.last_check_at,
        next_check_at=row.next_check_at,
        metadata=row.metadata
    )