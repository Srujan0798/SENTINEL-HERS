from datetime import datetime
from enum import Enum
from typing import Dict, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


class ServiceHealth(BaseModel):
    id: UUID
    team_id: UUID
    service_name: str
    status: HealthStatus = HealthStatus.UNKNOWN
    uptime_percentage: Optional[float] = None
    latency_ms: Optional[int] = None
    last_check_at: datetime
    next_check_at: Optional[datetime] = None
    metadata: Dict = {}
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ServiceHealthCreate(BaseModel):
    team_id: UUID
    service_name: str = Field(..., description="Service name to monitor")
    metadata: Dict = {}


class ServiceHealthResponse(BaseModel):
    id: UUID
    team_id: UUID
    service_name: str
    status: HealthStatus
    uptime_percentage: Optional[float]
    latency_ms: Optional[int]
    last_check_at: datetime
    next_check_at: Optional[datetime]
    metadata: Dict