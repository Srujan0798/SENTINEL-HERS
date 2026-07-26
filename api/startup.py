"""Run DB migrations on startup — creates all tables if they don't exist."""
import logging

logger = logging.getLogger(__name__)


def run_migrations() -> None:
    """Create all tables via the shared engine (idempotent — safe every startup)."""
    # Import all ORM models so Base.metadata knows every table
    import src.backend.shared_models  # noqa
    from src.backend.logs import models as _lm  # noqa
    from src.backend.incidents import models as _im  # noqa
    from src.backend.health import models as _hm  # noqa
    from src.backend.integrations.github import models as _gm  # noqa
    from src.backend.tasks import models as _tm  # noqa
    from src.backend.comms import models as _cm  # noqa

    from src.backend.db import Base, engine
    from sqlalchemy.orm import Session

    Base.metadata.create_all(bind=engine)

    # Seed default roles if the roles table is empty
    with Session(engine) as session:
        from src.backend.shared_models import RoleModel
        existing = session.query(RoleModel).first()
        if not existing:
            session.add_all([
                RoleModel(name="admin", permissions=["*"], description="Full system access"),
                RoleModel(name="incident_commander", permissions=["incidents:*", "tasks:*", "channels:*", "sla:*"], description="Lead incident response"),
                RoleModel(name="responder", permissions=["incidents:read", "incidents:update", "tasks:read", "tasks:update", "channels:read", "channels:write"], description="Respond to incidents"),
                RoleModel(name="viewer", permissions=["*:read"], description="Read-only access"),
            ])
            session.commit()
            logger.info("Default roles seeded")

    # Create performance indexes (idempotent — IF NOT EXISTS)
    try:
        _ensure_indexes(engine)
    except Exception as e:
        logger.warning("Index creation failed (non-fatal): %s", e)

    logger.info("DB migrations complete — %d tables", len(Base.metadata.tables))

    # Restore AI provider settings from DB (survives restarts).
    try:
        with Session(engine) as session:
            from src.backend.ai.settings import load_ai_settings_from_db
            load_ai_settings_from_db(session)
    except Exception:
        logger.exception("AI settings restore failed (non-fatal)")

    # Ensure judge demo path exists after every boot (idempotent).
    try:
        from src.backend.seed.service import auto_seed_if_enabled

        auto_seed_if_enabled()
    except Exception:
        logger.exception("Auto demo seed failed (non-fatal)")

def _ensure_indexes(engine) -> None:
    """Create performance indexes idempotently (IF NOT EXISTS)."""
    from sqlalchemy import text
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_incidents_team_id ON incidents(team_id)",
        "CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status)",
        "CREATE INDEX IF NOT EXISTS idx_incidents_severity ON incidents(severity)",
        "CREATE INDEX IF NOT EXISTS idx_incidents_detected_at ON incidents(detected_at)",
        "CREATE INDEX IF NOT EXISTS idx_tasks_team_id ON tasks(team_id)",
        "CREATE INDEX IF NOT EXISTS idx_tasks_incident_id ON tasks(incident_id)",
        "CREATE INDEX IF NOT EXISTS idx_timeline_events_incident_id ON timeline_events(incident_id)",
        "CREATE INDEX IF NOT EXISTS idx_log_entries_team_id ON log_entries(team_id)",
        "CREATE INDEX IF NOT EXISTS idx_log_entries_level ON log_entries(level)",
        "CREATE INDEX IF NOT EXISTS idx_log_entries_created_at ON log_entries(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_alerts_team_id ON alerts(team_id)",
        "CREATE INDEX IF NOT EXISTS idx_deployments_team_id ON deployments(team_id)",
        "CREATE INDEX IF NOT EXISTS idx_deployments_deployed_at ON deployments(deployed_at)",
    ]
    with engine.connect() as conn:
        for stmt in indexes:
            try:
                conn.execute(text(stmt))
            except Exception:
                pass
        try:
            conn.commit()
        except Exception:
            pass
    logger.info("Performance indexes ensured (%d statements)", len(indexes))
