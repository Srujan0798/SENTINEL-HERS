"""Security & tenancy integration tests.
Tests that unauth endpoints return 401 and cross-tenant access is blocked.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.backend.auth.dependencies import get_current_user_dependency
from src.backend.health import models as _health_models  # noqa: F401 — register tables
from src.backend.incidents import models as _incident_models  # noqa: F401
from src.backend.integrations.github import models as _github_models  # noqa: F401
from src.backend.tasks import models as _task_models  # noqa: F401
from src.backend.comms import models as _comms_models  # noqa: F401
from src.backend.logs import models as _log_models  # noqa: F401
from src.backend.db import Base, get_db
from api.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_security.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


client = TestClient(app)
TEAM_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
TEAM_B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
USER_ID = "00000000-0000-0000-0000-000000000099"


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    yield
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture(autouse=True)
def clean_and_seed():
    yield
    for table in ("incidents", "service_health", "timeline_events", "tasks"):
        try:
            with engine.connect() as conn:
                conn.execute(text(f"DELETE FROM {table}"))
                conn.commit()
        except Exception:
            pass


class TestUnauthenticatedEndpoints:
    """Endpoints that previously had no auth requirement must now return 401."""

    def test_health_list_requires_auth(self):
        app.dependency_overrides.pop(get_current_user_dependency, None)
        try:
            response = client.get("/api/health/services/")
            assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        finally:
            app.dependency_overrides[get_current_user_dependency] = lambda: {
                "id": USER_ID, "team_id": TEAM_A, "role": "admin",
                "email": "admin@test.com", "is_active": True,
            }

    def test_health_register_requires_auth(self):
        app.dependency_overrides.pop(get_current_user_dependency, None)
        try:
            response = client.post(
                "/api/health/services/",
                json={"team_id": TEAM_A, "service_name": "test-svc"},
            )
            assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        finally:
            app.dependency_overrides[get_current_user_dependency] = lambda: {
                "id": USER_ID, "team_id": TEAM_A, "role": "admin",
                "email": "admin@test.com", "is_active": True,
            }


class TestCrossTenantIsolation:
    """Authenticated users from one team must not see/access another team's data."""

    def test_health_list_team_isolation(self):
        app.dependency_overrides[get_current_user_dependency] = lambda: {
            "id": USER_ID, "team_id": TEAM_A, "role": "admin",
            "email": "admin@test.com", "is_active": True,
        }
        response = client.get("/api/health/services/")
        assert response.status_code == 200
        data = response.json()
        for svc in data:
            assert svc["team_id"] == TEAM_A, f"Found data from team {svc['team_id']} instead of {TEAM_A}"


class TestRBACEndpointProtection:
    """Viewer role must not be able to create/update/delete resources."""

    def test_viewer_cannot_create_incident(self):
        app.dependency_overrides[get_current_user_dependency] = lambda: {
            "id": USER_ID, "team_id": TEAM_A, "role": "viewer",
            "email": "viewer@test.com", "is_active": True,
        }
        response = client.post(
            "/api/incidents",
            json={"title": "Test", "severity": "SEV1"},
        )
        assert response.status_code == 403, f"Expected 403, got {response.status_code}"

    def test_viewer_cannot_update_incident(self):
        app.dependency_overrides[get_current_user_dependency] = lambda: {
            "id": USER_ID, "team_id": TEAM_A, "role": "viewer",
            "email": "viewer@test.com", "is_active": True,
        }
        response = client.patch(
            f"/api/incidents/00000000-0000-0000-0000-000000000001",
            json={"title": "Hacked"},
        )
        assert response.status_code in (403, 404), f"Expected 403 or 404, got {response.status_code}"

    def test_viewer_cannot_create_task(self):
        app.dependency_overrides[get_current_user_dependency] = lambda: {
            "id": USER_ID, "team_id": TEAM_A, "role": "viewer",
            "email": "viewer@test.com", "is_active": True,
        }
        response = client.post(
            f"/api/incidents/00000000-0000-0000-0000-000000000001/tasks",
            json={"title": "Viewer task", "priority": "high"},
        )
        assert response.status_code in (403, 404), f"Expected 403 or 404, got {response.status_code}"

    def test_viewer_cannot_assign_incident(self):
        app.dependency_overrides[get_current_user_dependency] = lambda: {
            "id": USER_ID, "team_id": TEAM_A, "role": "viewer",
            "email": "viewer@test.com", "is_active": True,
        }
        response = client.post(
            f"/api/incidents/00000000-0000-0000-0000-000000000001/assign",
            json={"user_id": USER_ID},
        )
        assert response.status_code in (403, 404), f"Expected 403 or 404, got {response.status_code}"
