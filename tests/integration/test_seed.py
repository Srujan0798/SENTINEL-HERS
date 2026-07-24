"""Integration tests for idempotent demo seed."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_seed.db")
os.environ.setdefault("JWT_SECRET", "test-secret-key-long-enough-32ch!!")
os.environ.setdefault("JWT_REFRESH_SECRET", "test-refresh-long-enough-32ch!!")
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("AI_PROVIDER", "mock")
os.environ.setdefault("AUTO_SEED_DEMO", "false")
os.environ.setdefault("ENV", "development")
os.environ.setdefault("SEED_SECRET", "test-seed-secret")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import src.backend.shared_models  # noqa
from src.backend.incidents import models as _im  # noqa
from src.backend.logs import models as _lm  # noqa
from src.backend.integrations.github import models as _gm  # noqa
from src.backend.tasks import models as _tm  # noqa
from src.backend.db import Base, get_db
from src.backend.seed.service import ensure_demo_seed, DEMO_EMAIL, DEMO_PASSWORD
from api.main import app

engine = create_engine("sqlite:///./test_seed.db", connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def setup_db():
    app.dependency_overrides[get_db] = override_db
    Base.metadata.create_all(bind=engine)
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    Path("test_seed.db").unlink(missing_ok=True)


def test_ensure_demo_seed_creates_sev1_and_resolved():
    db = TestingSession()
    try:
        result = ensure_demo_seed(db)
        assert result["status"] == "seeded"
        assert result.get("incident_id")

        # Idempotent second call
        result2 = ensure_demo_seed(db)
        assert result2["status"] == "skipped"

        from src.backend.incidents.models import Incident

        incidents = db.query(Incident).all()
        assert len(incidents) >= 3
        sev1 = [i for i in incidents if i.severity == "SEV1"]
        resolved = [i for i in incidents if i.status == "resolved" and i.resolved_at]
        assert sev1, "SEV1 required for demo path"
        assert resolved, "resolved incident required for MTTR"
    finally:
        db.close()


def test_http_seed_and_login():
    resp = client.post("/api/seed", headers={"X-Seed-Secret": "test-seed-secret"})
    assert resp.status_code in (200, 201)
    body = resp.json()
    assert body["status"] in ("seeded", "skipped")

    login = client.post(
        "/auth/login",
        json={"email": DEMO_EMAIL, "password": DEMO_PASSWORD},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    incidents = client.get("/api/incidents?per_page=20", headers=headers)
    assert incidents.status_code == 200
    data = incidents.json()["data"]
    assert len(data) >= 1
    assert any(i.get("severity") == "SEV1" for i in data)

    summary = client.get("/api/analytics/incidents/summary", headers=headers)
    assert summary.status_code == 200
    s = summary.json()
    assert s.get("total_incidents", 0) >= 1
