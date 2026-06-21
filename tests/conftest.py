import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Point all modules at shared SQLite test DB
os.environ.setdefault("DATABASE_URL", "sqlite:///./sentinel_test.db")
os.environ.setdefault("JWT_SECRET", "test-secret-key-long-enough-32ch!!")
os.environ.setdefault("JWT_REFRESH_SECRET", "test-refresh-long-enough-32ch!!")
os.environ.setdefault("REDIS_URL", "")

import pytest  # noqa: E402


def _import_orm_models():
    """Import all ORM models so Base.metadata knows all tables."""
    try:
        import src.backend.shared_models as _sm  # noqa — registers teams/users/incidents stubs
    except Exception:
        pass
    try:
        from src.backend.logs import models as _lm  # noqa
    except Exception:
        pass
    try:
        from src.backend.incidents import models as _im  # noqa — registers incidents table
    except Exception:
        pass
    try:
        from src.backend.health import models as _hm  # noqa
    except Exception:
        pass
    try:
        from src.backend.integrations.github import models as _gm  # noqa
    except Exception:
        pass
    try:
        from src.backend.tasks import models as _tm  # noqa
    except Exception:
        pass
    try:
        from src.backend.comms import models as _cm  # noqa
    except Exception:
        pass


_import_orm_models()




@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    """Create all tables once per test session on SQLite."""
    from sqlalchemy import create_engine
    from src.backend.db import Base
    _import_orm_models()
    db_path = "sentinel_test.db"
    engine = create_engine(
        f"sqlite:///./{db_path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    Path(db_path).unlink(missing_ok=True)
