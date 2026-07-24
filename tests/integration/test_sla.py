"""Integration tests for task management and SLA engine."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_sla.db")
os.environ.setdefault("JWT_SECRET", "test-secret-key-long-enough-32ch!!")
os.environ.setdefault("JWT_REFRESH_SECRET", "test-refresh-long-enough-32ch!!")
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("AI_PROVIDER", "mock")

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
from api.main import app

engine = create_engine("sqlite:///./test_sla.db", connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


client = TestClient(app)

_email_counter = [0]


@pytest.fixture(autouse=True, scope="module")
def setup_db():
    app.dependency_overrides[get_db] = override_db
    Base.metadata.create_all(bind=engine)
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    Path("test_sla.db").unlink(missing_ok=True)


@pytest.fixture
def auth():
    _email_counter[0] += 1
    email = f"sla{_email_counter[0]}@sentinel.io"
    resp = client.post("/auth/register", json={
        "email": email, "password": "testpassword123",
        "name": "SLA Tester", "team_name": f"SLA Team {_email_counter[0]}",
    })
    assert resp.status_code == 201
    data = resp.json()
    return {
        "headers": {"Authorization": f"Bearer {data['access_token']}"},
        "team_id": data["user"]["team_id"],
        "user_id": data["user"]["id"],
    }


@pytest.fixture
def incident_id(auth):
    resp = client.post(
        "/api/incidents",
        json={"title": "DB connection pool exhausted", "severity": "SEV2"},
        params={"team_id": auth["team_id"]},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


class TestTaskCRUD:
    def test_create_task(self, auth, incident_id):
        resp = client.post(
            f"/api/incidents/{incident_id}/tasks",
            json={"title": "Check DB connection limits", "priority": "high"},
            headers=auth["headers"],
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Check DB connection limits"
        assert data["status"] == "open"
        assert data["priority"] == "high"
        assert data["incident_id"] == incident_id

    def test_list_tasks(self, auth, incident_id):
        client.post(
            f"/api/incidents/{incident_id}/tasks",
            json={"title": "Task A"},
            headers=auth["headers"],
        )
        client.post(
            f"/api/incidents/{incident_id}/tasks",
            json={"title": "Task B"},
            headers=auth["headers"],
        )
        resp = client.get(f"/api/incidents/{incident_id}/tasks", headers=auth["headers"])
        assert resp.status_code == 200
        tasks = resp.json()
        assert isinstance(tasks, list)
        assert len(tasks) >= 2

    def test_update_task_status(self, auth, incident_id):
        create_resp = client.post(
            f"/api/incidents/{incident_id}/tasks",
            json={"title": "Fix connection pool"},
            headers=auth["headers"],
        )
        task_id = create_resp.json()["id"]

        resp = client.patch(
            f"/api/tasks/{task_id}",
            json={"status": "completed"},
            headers=auth["headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"
        assert resp.json()["completed_at"] is not None

    def test_assign_task(self, auth, incident_id):
        create_resp = client.post(
            f"/api/incidents/{incident_id}/tasks",
            json={"title": "Investigate root cause"},
            headers=auth["headers"],
        )
        task_id = create_resp.json()["id"]

        resp = client.patch(
            f"/api/tasks/{task_id}",
            json={"assigned_to": auth["user_id"]},
            headers=auth["headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["assigned_to"] == auth["user_id"]

    def test_update_nonexistent_task(self, auth):
        resp = client.patch(
            "/api/tasks/00000000-0000-0000-0000-000000000000",
            json={"status": "completed"},
            headers=auth["headers"],
        )
        assert resp.status_code == 404

    def test_tasks_unauthorized(self, incident_id):
        resp = client.get(f"/api/incidents/{incident_id}/tasks")
        assert resp.status_code in (401, 403)


class TestSLAStatus:
    def test_sla_list_returns_open_incidents(self, auth, incident_id):
        resp = client.get("/api/sla", headers=auth["headers"])
        assert resp.status_code == 200
        items = resp.json()
        assert isinstance(items, list)
        assert len(items) >= 1
        item = next((i for i in items if i["incident_id"] == incident_id), None)
        assert item is not None
        assert "remaining_minutes" in item
        assert "breached" in item
        assert "sla_minutes" in item

    def test_sla_policy_correct(self, auth):
        from src.backend.sla.policy import sla_minutes_for
        assert sla_minutes_for("SEV1") == 15
        assert sla_minutes_for("SEV2") == 60
        assert sla_minutes_for("SEV3") == 240
        assert sla_minutes_for("SEV4") == 1440

    def test_sla_remaining_time_decreases(self, auth):
        from src.backend.sla.policy import sla_minutes_for, time_remaining_minutes
        from datetime import datetime, timezone, timedelta

        # Detected 10 min ago for SEV1 (15 min SLA) → 5 min remaining
        detected = datetime.now(timezone.utc) - timedelta(minutes=10)
        remaining = time_remaining_minutes(detected, "SEV1")
        assert 4 < remaining < 6  # ~5 minutes left

    def test_sla_breach_detection(self, auth):
        from src.backend.sla.policy import time_remaining_minutes
        from datetime import datetime, timezone, timedelta

        # SEV1 detected 20 min ago → should be breached
        detected = datetime.now(timezone.utc) - timedelta(minutes=20)
        remaining = time_remaining_minutes(detected, "SEV1")
        assert remaining < 0  # breached

    def test_sla_unauthorized(self):
        resp = client.get("/api/sla")
        assert resp.status_code in (401, 403)
