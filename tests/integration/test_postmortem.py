"""Integration tests for AI postmortem report generation."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_postmortem.db")
os.environ.setdefault("JWT_SECRET", "test-secret-key-long-enough-32ch!!")
os.environ.setdefault("JWT_REFRESH_SECRET", "test-refresh-long-enough-32ch!!")
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("AI_PROVIDER", "mock")

import uuid
from datetime import datetime, timezone

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

engine = create_engine("sqlite:///./test_postmortem.db", connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


client = TestClient(app)
_ctr = [0]


@pytest.fixture(autouse=True, scope="module")
def setup_db():
    app.dependency_overrides[get_db] = override_db
    Base.metadata.create_all(bind=engine)
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    Path("test_postmortem.db").unlink(missing_ok=True)


@pytest.fixture
def auth():
    _ctr[0] += 1
    resp = client.post("/auth/register", json={
        "email": f"postmortem{_ctr[0]}@sentinel.io",
        "password": "testpassword123",
        "name": "Postmortem Tester",
        "team_name": f"Postmortem Team {_ctr[0]}",
    })
    assert resp.status_code == 201
    data = resp.json()
    return {
        "headers": {"Authorization": f"Bearer {data['access_token']}"},
        "team_id": data["user"]["team_id"],
    }


def _create_incident(db, team_id, **kwargs):
    defaults = dict(
        id=str(uuid.uuid4()),
        team_id=team_id,
        title="Test incident",
        description="For postmortem testing",
        severity="SEV2",
        status="resolved",
        detected_at=datetime.now(timezone.utc),
        resolved_at=datetime.now(timezone.utc),
        ai_root_cause_ranking=[
            {"hypothesis": "Database connection pool exhausted", "confidence": 0.85, "suggested_action": "Increase pool size"},
            {"hypothesis": "Network latency spike", "confidence": 0.65, "suggested_action": "Add CDN"},
        ],
    )
    defaults.update(kwargs)
    inc = _im.Incident(**defaults)
    db.add(inc)
    db.commit()
    return inc


def _create_timeline_event(db, incident_id, **kwargs):
    defaults = dict(
        id=str(uuid.uuid4()),
        incident_id=incident_id,
        event_type="detected",
        source="system",
        actor="system",
        ts=datetime.now(timezone.utc),
        description="Incident detected by monitoring",
    )
    defaults.update(kwargs)
    from src.backend.incidents.models import TimelineEvent
    event = TimelineEvent(**defaults)
    db.add(event)
    db.commit()


def _create_log(db, team_id, **kwargs):
    defaults = dict(
        id=uuid.uuid4(),
        team_id=team_id,
        incident_id=None,
        service="api-gateway",
        level="error",
        message="timeout upstream",
        created_at=datetime.now(timezone.utc),
        indexed_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    log = _lm.LogEntryModel(**defaults)
    db.add(log)
    db.commit()
    return log


class TestPostmortemEndpoint:
    def test_postmortem_returns_all_sections(self, auth):
        db = TestingSession()
        try:
            inc = _create_incident(db, auth["team_id"])
            _create_timeline_event(db, inc.id)
            inc_id = str(inc.id)
        finally:
            db.close()

        resp = client.get(f"/api/ai/postmortem/{inc_id}", headers=auth["headers"])
        assert resp.status_code == 200
        data = resp.json()
        assert data["incident_id"] == inc_id
        assert "content" in data
        assert "sections" in data
        assert len(data["sections"]) > 0 or "[mock-ai]" in data["content"]

    def test_postmortem_markdown_format(self, auth):
        db = TestingSession()
        try:
            inc = _create_incident(db, auth["team_id"])
            inc_id = str(inc.id)
        finally:
            db.close()

        resp = client.get(f"/api/ai/postmortem/{inc_id}?format=md", headers=auth["headers"])
        assert resp.status_code == 200
        assert resp.headers.get("content-type", "").startswith("text/markdown")
        assert "Content-Disposition" in resp.headers
        assert resp.text.startswith("#") or resp.text.startswith("##") or "[mock-ai]" in resp.text

    def test_postmortem_incident_not_found(self, auth):
        resp = client.get(f"/api/ai/postmortem/{uuid.uuid4()}", headers=auth["headers"])
        assert resp.status_code == 404

    def test_postmortem_requires_auth(self):
        resp = client.get(f"/api/ai/postmortem/{uuid.uuid4()}")
        assert resp.status_code in (401, 403)

    def test_postmortem_cross_tenant_blocked(self, auth):
        db = TestingSession()
        try:
            inc_other = _create_incident(db, "other-team-id")
            other_id = str(inc_other.id)
        finally:
            db.close()

        resp = client.get(f"/api/ai/postmortem/{other_id}", headers=auth["headers"])
        assert resp.status_code == 404

    def test_postmortem_includes_timeline_and_root_causes(self, auth):
        db = TestingSession()
        try:
            inc = _create_incident(db, auth["team_id"], title="API latency spike")
            inc_id = str(inc.id)
            _create_timeline_event(db, inc_id, event_type="detected", description="Latency > 2s")
            _create_timeline_event(db, inc_id, event_type="mitigated", description="Scaled up replicas")
            _create_log(db, auth["team_id"], incident_id=inc_id, message="timeout connecting to payment service")
        finally:
            db.close()

        resp = client.get(f"/api/ai/postmortem/{inc_id}", headers=auth["headers"])
        assert resp.status_code == 200
        data = resp.json()
        assert data["incident_id"] == inc_id
        assert len(data["content"]) > 0
