import asyncio
import logging
import os
import aiohttp
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import Dict, Any
import json

from src.backend.health.models import ServiceHealth

logger = logging.getLogger(__name__)


class ServiceHealthProbe:
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/sentinel")
        self.engine = create_engine(self.database_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.realtime_hub_url = os.getenv("REALTIME_HUB_URL", "http://localhost:8000/realtime/hub")

    async def check_service(self, service_name: str, team_id: str) -> Dict[str, Any]:
        """Check a single service and return health metrics"""
        start_time = datetime.now()
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                url = f"http://{service_name}:8000/healthz"
                async with session.get(url) as response:
                    latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                    
                    if response.status == 200:
                        status = "healthy"
                        uptime_pct = 100.0
                    elif response.status >= 500:
                        status = "down"
                        uptime_pct = 0.0
                    else:
                        status = "degraded"
                        uptime_pct = 95.0
                    
                    return {
                        "status": status,
                        "latency_ms": latency_ms,
                        "uptime_percentage": uptime_pct,
                        "success": True
                    }
        except Exception as e:
            latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            return {
                "status": "down",
                "latency_ms": latency_ms,
                "uptime_percentage": 0.0,
                "success": False,
                "error": str(e)
            }

    async def update_service_health(self, service_name: str, team_id: str, result: Dict[str, Any]):
        """Update service health in database and emit realtime event if status changed"""
        db = self.SessionLocal()
        try:
            row = db.execute(text("""
                SELECT status, latency_ms, uptime_percentage
                FROM service_health
                WHERE service_name = :service_name AND team_id = :team_id
            """), {"service_name": service_name, "team_id": team_id}).fetchone()
            
            if row:
                previous_status = row.status
                
                db.execute(text("""
                    UPDATE service_health
                    SET status = :status,
                        uptime_percentage = :uptime_percentage,
                        latency_ms = :latency_ms,
                        last_check_at = NOW(),
                        next_check_at = NOW() + INTERVAL '30 minutes',
                        metadata = jsonb_set(COALESCE(metadata, '{}'), '{last_check}', to_jsonb(NOW()))
                    WHERE service_name = :service_name AND team_id = :team_id
                """), {
                    "service_name": service_name,
                    "team_id": team_id,
                    "status": result["status"],
                    "uptime_percentage": result["uptime_percentage"],
                    "latency_ms": result["latency_ms"]
                })
                
                current_status = result["status"]
                if previous_status != current_status:
                    self.emit_health_change_event(service_name, team_id, previous_status, current_status)
            else:
                db.execute(text("""
                    INSERT INTO service_health (team_id, service_name, status, uptime_percentage, latency_ms, last_check_at, next_check_at)
                    VALUES (:team_id, :service_name, :status, :uptime_percentage, :latency_ms, NOW(), NOW() + INTERVAL '30 minutes')
                """), {
                    "team_id": team_id,
                    "service_name": service_name,
                    "status": result["status"],
                    "uptime_percentage": result["uptime_percentage"],
                    "latency_ms": result["latency_ms"]
                })
            
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def emit_health_change_event(self, service_name: str, team_id: str, previous_status: str, new_status: str):
        """Emit realtime event for health status change"""
        try:
            event_data = {
                "event_type": "service.health_changed",
                "service_name": service_name,
                "team_id": team_id,
                "previous_status": previous_status,
                "new_status": new_status,
                "timestamp": datetime.now().isoformat()
            }
            
            import requests
            response = requests.post(self.realtime_hub_url, json=event_data, timeout=5)
            if response.status_code == 200:
                logger.info("Emitted health change event: %s %s -> %s", service_name, previous_status, new_status)
            else:
                logger.warning("Failed to emit health change event: %s", response.status_code)
        except Exception as e:
            logger.error("Error emitting health change event: %s", e)

    async def probe_all_services(self):
        """Probe all registered services"""
        db = self.SessionLocal()
        try:
            result = db.execute(text("""
                SELECT DISTINCT team_id, service_name
                FROM service_health
                WHERE status != 'down' OR last_check_at < NOW() - INTERVAL '1 hour'
            """))
            
            services = result.fetchall()
            
            for row in services:
                team_id = row.team_id
                service_name = row.service_name
                
                result = await self.check_service(service_name, team_id)
                await self.update_service_health(service_name, team_id, result)
                
        finally:
            db.close()

    async def start_probing(self, interval_seconds: int = 30):
        """Start continuous probing"""
        while True:
            try:
                await self.probe_all_services()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error("Error in service probing: %s", e)
                await asyncio.sleep(interval_seconds)


async def start_health_prober():
    """Start the health prober as a background task"""
    probe = ServiceHealthProbe()
    asyncio.create_task(probe.start_probing())