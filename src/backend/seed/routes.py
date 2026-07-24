import logging
import os
import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from src.backend.db import get_db
from src.backend.shared_models import UserModel, TeamModel, RoleModel
from src.backend.incidents.models import Incident, TimelineEvent
from src.backend.incidents.enums import IncidentStatus, SeverityLevel
from src.backend.tasks.models import Task
from src.backend.logs.models import LogEntryModel, AlertModel
from src.backend.auth.service import hash_password

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["seed"])

SEED_SECRET = os.getenv("SEED_SECRET", "sentinel-seed-2026")


def _get_or_create_team(db: Session, name: str) -> TeamModel:
    slug = name.lower().replace(" ", "-")
    team = db.query(TeamModel).filter(TeamModel.slug == slug).first()
    if team:
        return team
    team = TeamModel(
        id=str(uuid.uuid4()),
        name=name,
        slug=f"{slug}-{uuid.uuid4().hex[:8]}",
        created_at=datetime.now(timezone.utc),
    )
    db.add(team)
    db.flush()
    return team


def _get_or_create_user(db: Session, team: TeamModel) -> UserModel:
    user = db.query(UserModel).filter(UserModel.email == "demo@sentinel.io").first()
    if user:
        return user
    admin_role = db.query(RoleModel).filter(RoleModel.name == "admin").first()
    user = UserModel(
        id=str(uuid.uuid4()),
        team_id=str(team.id),
        email="demo@sentinel.io",
        password_hash=hash_password("Sentinel2026!"),
        name="Demo User",
        role_id=str(admin_role.id) if admin_role else None,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.flush()
    return user


@router.post("/seed", status_code=201)
async def seed_demo(
    x_seed_secret: str = Header(None),
    x_ai_provider: str | None = Header(None),
    x_openrouter_key: str | None = Header(None),
    x_nvapi_key: str | None = Header(None),
    db: Session = Depends(get_db),
):
    if not x_seed_secret or x_seed_secret != SEED_SECRET:
        raise HTTPException(status_code=403, detail="Invalid seed secret")

    if x_ai_provider:
        os.environ["AI_PROVIDER"] = x_ai_provider
    if x_openrouter_key:
        os.environ["OPENROUTER_API_KEY"] = x_openrouter_key
    if x_nvapi_key:
        os.environ["NVAPI_KEY"] = x_nvapi_key

    try:
        team = _get_or_create_team(db, "Acme SRE")
        user = _get_or_create_user(db, team)
        team_id = str(team.id)

        existing = db.query(Incident).filter(Incident.team_id == team_id).first()
        if existing:
            return {"status": "skipped", "reason": "demo data already present"}

        now = datetime.now(timezone.utc)

        log_entries_data = [
            {"service": "api-gateway", "level": "error", "message": "Database connection pool exhausted after 30s", "ts": now - timedelta(minutes=30)},
            {"service": "payments", "level": "error", "message": "Payment service timeout: upstream response > 5000ms", "ts": now - timedelta(minutes=25)},
            {"service": "redis-cache", "level": "warn", "message": "Redis cache miss rate spike: 94% miss ratio", "ts": now - timedelta(minutes=20)},
            {"service": "api-gateway", "level": "info", "message": "API gateway latency p99 > 2000ms", "ts": now - timedelta(minutes=15)},
            {"service": "auth", "level": "error", "message": "Auth service: JWT validation failed for 1234 requests", "ts": now - timedelta(minutes=10)},
            {"service": "payments-worker", "level": "fatal", "message": "CRITICAL: Pod crash-loop detected in payments-worker", "ts": now - timedelta(minutes=5)},
        ]
        for entry in log_entries_data:
            db.add(LogEntryModel(
                id=uuid.uuid4(),
                team_id=team_id,
                service=entry["service"],
                level=entry["level"],
                message=entry["message"],
                created_at=entry["ts"],
            ))
        db.flush()
        logger.info("Seed: %d log entries ingested", len(log_entries_data))

        def make_incident(title: str, desc: str, severity: str) -> Incident:
            inc = Incident(
                id=str(uuid.uuid4()),
                team_id=team_id,
                title=title,
                description=desc,
                severity=severity,
                status=IncidentStatus.DETECTED.value,
                detected_at=now,
            )
            db.add(inc)
            db.flush()
            return inc

        inc1 = make_incident(
            "Payment service cascade failure",
            "Payment service is returning 503s due to database connection pool exhaustion. Error rate at 78%, p99 latency > 5s. Revenue impact estimated at $12k/min.",
            "SEV1",
        )
        inc2 = make_incident(
            "Redis cache miss rate spike",
            "Cache miss ratio jumped from 5% to 94% after last deployment. Causing increased database load across all services.",
            "SEV2",
        )
        inc3 = make_incident(
            "Auth service elevated error rate",
            "JWT validation failures spiking. 1234 failed auth requests in last 15 minutes.",
            "SEV3",
        )
        logger.info("Seed: 3 incidents created")

        timeline = [
            ("detection", "PagerDuty alert fired: payment error rate > 50%"),
            ("acknowledgement", "On-call engineer paged and acknowledged"),
            ("investigation", "Root cause narrowed to DB connection pool exhaustion after cache flush"),
            ("mitigation", "Connection pool size increased from 10 to 50; error rate dropping"),
        ]
        for ev_type, ev_desc in timeline:
            db.add(TimelineEvent(
                id=str(uuid.uuid4()),
                incident_id=inc1.id,
                event_type=ev_type,
                source="seed",
                actor="system",
                description=ev_desc,
                ts=now,
            ))
        db.flush()
        logger.info("Seed: 4 timeline events added")

        tasks_data = [
            ("Increase DB connection pool size in prod", "high"),
            ("Add circuit breaker to payments to DB calls", "high"),
            ("Set up Redis eviction alerts", "medium"),
            ("Update runbook for cache-flush incidents", "low"),
        ]
        for task_title, task_priority in tasks_data:
            db.add(Task(
                id=str(uuid.uuid4()),
                team_id=team_id,
                incident_id=inc1.id,
                title=task_title,
                priority=task_priority,
                status="open",
            ))
        db.flush()
        logger.info("Seed: 4 tasks created")

        alerts_data = [
            {"source": "prometheus", "alert_type": "HighErrorRate", "title": "Error rate > 50% for payments service", "severity": "critical"},
            {"source": "kubernetes", "alert_type": "PodCrashLoop", "title": "payments-worker crash-looping (8 restarts)", "severity": "critical"},
            {"source": "datadog", "alert_type": "HighLatency", "title": "p99 API latency > 2s", "severity": "warning"},
        ]
        for alert in alerts_data:
            db.add(AlertModel(
                id=uuid.uuid4(),
                team_id=team_id,
                source=alert["source"],
                alert_type=alert["alert_type"],
                title=alert["title"],
                severity=alert["severity"],
            ))
        db.flush()
        logger.info("Seed: 3 alerts created")

        try:
            from src.backend.ml.anomaly.service import AnomalyService
            ml_svc = AnomalyService()
            metrics_to_score = [
                ("payments", [0.92]),
                ("api-gateway", [0.85]),
                ("redis-cache", [0.97]),
                ("auth", [0.35]),
                ("notifications", [0.28]),
            ]
            for svc_name, vals in metrics_to_score:
                ml_svc.score(svc_name, vals, team_id=team_id)
            logger.info("Seed: anomaly scores seeded")
        except Exception as e:
            logger.warning("Seed: anomaly scoring skipped (%s)", e)

        db.commit()
        return {
            "status": "seeded",
            "team_id": team_id,
            "incident_id": inc1.id,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.exception("Seed failed")
        raise HTTPException(status_code=500, detail=f"Seed error: {e}")
