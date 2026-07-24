import logging
import os
import datetime
from fastapi import APIRouter, HTTPException, Header, Depends
from sqlalchemy.orm import Session
from src.backend.db import get_db
from src.backend.auth.dependencies import get_current_user_dependency

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["seed"])

SEED_SECRET = os.getenv("SEED_SECRET", "sentinel-seed-2026")


def run_seed(db: Session):
    from src.backend.auth.service import AuthService
    from src.backend.incidents.service import IncidentService
    from src.backend.logs.service import LogService
    from src.backend.tasks.service import TaskService

    auth_svc = AuthService(db)
    inc_svc = IncidentService(db)
    log_svc = LogService(db)
    task_svc = TaskService(db)

    user = auth_svc.register_user(
        email="demo@sentinel.io",
        password="Sentinel2026!",
        name="Demo User",
        team_name="Acme SRE",
    )
    if not user:
        user = auth_svc.authenticate_user(email="demo@sentinel.io", password="Sentinel2026!")
    if not user:
        raise HTTPException(status_code=500, detail="Seed: could not register/login demo user")

    team_id = user["team_id"]

    existing = inc_svc.list_incidents(team_id=team_id)
    if existing and len(existing) > 0:
        logger.info("Seed: demo data already present (%d incidents), skipping", len(existing))
        return {"status": "skipped", "reason": "demo data already present"}

    now = datetime.datetime.now(datetime.UTC)

    log_entries = [
        {"service": "api-gateway", "level": "error", "message": "Database connection pool exhausted after 30s", "timestamp": (now - datetime.timedelta(minutes=30)).isoformat(), "metadata": {"host": "prod-node-01", "env": "production"}},
        {"service": "payments", "level": "error", "message": "Payment service timeout: upstream response > 5000ms", "timestamp": (now - datetime.timedelta(minutes=25)).isoformat(), "metadata": {"host": "prod-node-02", "env": "production"}},
        {"service": "redis-cache", "level": "warn", "message": "Redis cache miss rate spike: 94% miss ratio", "timestamp": (now - datetime.timedelta(minutes=20)).isoformat(), "metadata": {"host": "prod-node-03", "env": "production"}},
        {"service": "api-gateway", "level": "info", "message": "API gateway latency p99 > 2000ms", "timestamp": (now - datetime.timedelta(minutes=15)).isoformat(), "metadata": {"host": "prod-node-04", "env": "production"}},
        {"service": "auth", "level": "error", "message": "Auth service: JWT validation failed for 1234 requests", "timestamp": (now - datetime.timedelta(minutes=10)).isoformat(), "metadata": {"host": "prod-node-05", "env": "production"}},
        {"service": "payments-worker", "level": "fatal", "message": "CRITICAL: Pod crash-loop detected in payments-worker", "timestamp": (now - datetime.timedelta(minutes=5)).isoformat(), "metadata": {"host": "prod-node-06", "env": "production"}},
    ]
    for entry in log_entries:
        log_svc.ingest_log(entry, team_id=team_id)
    logger.info("Seed: %d log entries ingested", len(log_entries))

    inc1 = inc_svc.create_incident(
        title="Payment service cascade failure",
        description="Payment service is returning 503s due to database connection pool exhaustion. Error rate at 78%, p99 latency > 5s. Revenue impact estimated at $12k/min.",
        severity="SEV1",
        team_id=team_id,
        actor="system",
    )
    inc2 = inc_svc.create_incident(
        title="Redis cache miss rate spike",
        description="Cache miss ratio jumped from 5% to 94% after last deployment. Causing increased database load across all services.",
        severity="SEV2",
        team_id=team_id,
        actor="system",
    )
    inc3 = inc_svc.create_incident(
        title="Auth service elevated error rate",
        description="JWT validation failures spiking. 1234 failed auth requests in last 15 minutes.",
        severity="SEV3",
        team_id=team_id,
        actor="system",
    )
    inc_ids = [i.id for i in [inc1, inc2, inc3] if i]
    logger.info("Seed: %d incidents created", len(inc_ids))

    inc_id = inc_ids[0]

    timeline_events = [
        {"event_type": "detection", "description": "PagerDuty alert fired: payment error rate > 50%"},
        {"event_type": "acknowledgement", "description": "On-call engineer paged and acknowledged"},
        {"event_type": "investigation", "description": "Root cause narrowed to DB connection pool exhaustion after cache flush"},
        {"event_type": "mitigation", "description": "Connection pool size increased from 10 to 50; error rate dropping"},
    ]
    for ev in timeline_events:
        inc_svc.add_timeline_event(incident_id=inc_id, team_id=team_id, **ev, actor="system")
    logger.info("Seed: %d timeline events added", len(timeline_events))

    tasks_data = [
        {"title": "Increase DB connection pool size in prod", "priority": "high"},
        {"title": "Add circuit breaker to payments to DB calls", "priority": "high"},
        {"title": "Set up Redis eviction alerts", "priority": "medium"},
        {"title": "Update runbook for cache-flush incidents", "priority": "low"},
    ]
    for task_data in tasks_data:
        task_svc.create_task(incident_id=inc_id, team_id=team_id, **task_data)
    logger.info("Seed: %d tasks created", len(tasks_data))

    try:
        from src.backend.ml.anomaly.service import AnomalyService
        ml_svc = AnomalyService()
        metrics = [
            {"service": "payments", "metrics": [0.92]},
            {"service": "api-gateway", "metrics": [0.85]},
            {"service": "redis-cache", "metrics": [0.97]},
            {"service": "auth", "metrics": [0.35]},
            {"service": "notifications", "metrics": [0.28]},
        ]
        for m in metrics:
            ml_svc.score(m["service"], m["metrics"], team_id=team_id)
        logger.info("Seed: anomaly scores seeded")
    except Exception as e:
        logger.warning("Seed: anomaly scoring skipped (%s)", e)

    return {"status": "seeded", "incidents": len(inc_ids), "team_id": team_id}


@router.post("/seed", status_code=201)
async def seed_demo(
    x_seed_secret: str = Header(None),
    db: Session = Depends(get_db),
):
    if not x_seed_secret or x_seed_secret != SEED_SECRET:
        raise HTTPException(status_code=403, detail="Invalid seed secret")
    result = run_seed(db)
    return result
