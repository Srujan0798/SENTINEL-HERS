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

    logger.info("DB migrations complete — %d tables", len(Base.metadata.tables))
