"""Integration tests for conversational AI chat — RAG over team logs and incidents."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_ai_chat.db")
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

engine = create_engine("sqlite:///./test_ai_chat.db", connect_args={"check_same_thread": False})
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
    Path("test_ai_chat.db").unlink(missing_ok=True)


@pytest.fixture(scope="class")
def team_a():
    _ctr[0] += 1
    resp = client.post("/auth/register", json={
        "email": f"chata{_ctr[0]}@sentinel.io",
        "password": "testpassword123",
        "name": "Team A User",
        "team_name": f"Chat Team A {_ctr[0]}",
    })
    assert resp.status_code == 201, f"team_a register failed: {resp.text}"
    data = resp.json()
    return {
        "headers": {"Authorization": f"Bearer {data['access_token']}"},
        "team_id": data["user"]["team_id"],
        "token": data["access_token"],
    }


@pytest.fixture(scope="class")
def team_b():
    _ctr[0] += 1
    resp = client.post("/auth/register", json={
        "email": f"chatb{_ctr[0]}@sentinel.io",
        "password": "testpassword123",
        "name": "Team B User",
        "team_name": f"Chat Team B {_ctr[0]}",
    })
    assert resp.status_code == 201, f"team_b register failed: {resp.text}"
    data = resp.json()
    return {
        "headers": {"Authorization": f"Bearer {data['access_token']}"},
        "team_id": data["user"]["team_id"],
        "token": data["access_token"],
    }


def _create_incident(db, team_id: str, title: str = "Test incident"):
    inc = _im.Incident(
        id=str(uuid.uuid4()),
        team_id=team_id,
        title=title,
        description="For testing chat retrieval",
        severity="SEV3",
        status="open",
        detected_at=datetime.now(timezone.utc),
    )
    db.add(inc)
    db.commit()
    return inc


def _create_log(db, team_id: str, incident_id: str | None = None, service: str = "api-gateway", message: str = "test log", level: str = "error"):
    log = _lm.LogEntryModel(
        id=uuid.uuid4(),
        team_id=team_id,
        incident_id=incident_id,
        service=service,
        level=level,
        message=message,
        created_at=datetime.now(timezone.utc),
        indexed_at=datetime.now(timezone.utc),
    )
    db.add(log)
    db.commit()
    return log


class TestChatEndpoint:
    def test_chat_returns_answer_with_citations(self, team_a):
        db = TestingSession()
        try:
            _create_incident(db, team_a["team_id"], title="Payment service outage")
            _create_log(db, team_a["team_id"], service="payments", message="timeout connecting to DB", level="error")
        finally:
            db.close()

        resp = client.post(
            "/api/ai/chat",
            json={"question": "What incidents do we have?"},
            headers=team_a["headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "citations" in data
        assert isinstance(data["citations"], list)
        assert len(data["answer"]) > 0
        assert data["confidence"] >= 0.0

    def test_chat_with_incident_id(self, team_a):
        db = TestingSession()
        try:
            inc = _create_incident(db, team_a["team_id"], title="DB connection failure")
            inc_id = str(inc.id)
            _create_log(db, team_a["team_id"], incident_id=inc_id, service="db-worker", message="connection refused", level="fatal")
        finally:
            db.close()

        resp = client.post(
            "/api/ai/chat",
            json={"question": "What happened with the DB?", "incident_id": inc_id},
            headers=team_a["headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert len(data["citations"]) > 0

    def test_chat_no_data_returns_fallback(self, team_a):
        resp = client.post(
            "/api/ai/chat",
            json={"question": "Tell me about everything"},
            headers=team_a["headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "don't have enough data" in data["answer"].lower() or "mock-ai" in data["answer"]

    def test_chat_requires_auth(self):
        resp = client.post("/api/ai/chat", json={"question": "hello"})
        assert resp.status_code in (401, 403)


class TestCrossTenantIsolation:
    def test_cross_tenant_no_data_leak(self, team_a, team_b):
        db = TestingSession()
        try:
            _create_incident(db, team_a["team_id"], title="TEAM-A-SECRET-INCIDENT")
            _create_log(db, team_a["team_id"], service="secret-svc", message="TEAM-A-SECRET-LOG", level="error")
        finally:
            db.close()

        resp = client.post(
            "/api/ai/chat",
            json={"question": "What incidents do we have?"},
            headers=team_b["headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "TEAM-A-SECRET-INCIDENT" not in data["answer"]
        assert "TEAM-A-SECRET-LOG" not in data["answer"]

    def test_cross_tenant_incident_id_rejected(self, team_a, team_b):
        db = TestingSession()
        try:
            inc = _create_incident(db, team_a["team_id"], title="Cross-tenant secret")
            inc_id = str(inc.id)
        finally:
            db.close()

        resp = client.post(
            "/api/ai/chat",
            json={"question": "Details?", "incident_id": inc_id},
            headers=team_b["headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "cross-tenant" not in data["answer"].lower()
        assert "secret" not in data["answer"].lower()
