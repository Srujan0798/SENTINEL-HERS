"""Integration tests for log ingestion, search, and alert CRUD."""

import random
import string
import time
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from src.backend.auth.routes import router as auth_router
from src.backend.ingest.routes import router as ingest_router
from src.backend.logs.database import SessionLocal, engine
from src.backend.logs.routes import router as logs_router


@pytest.fixture(scope="session")
def app():
    application = FastAPI()
    application.include_router(auth_router)
    application.include_router(ingest_router)
    application.include_router(logs_router)
    return application


@pytest.fixture(scope="session")
def client(app):
    return TestClient(app)


@pytest.fixture(scope="session")
def registered_user(client):
    resp = client.post(
        "/auth/register",
        json={
            "email": "logstest@sentinel.io",
            "password": "testpassword123",
            "name": "Logs Test User",
            "team_name": "Logs Test Team",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    return {
        "access_token": data["access_token"],
        "user_id": data["user"]["id"],
        "team_id": data["user"]["team_id"],
    }


@pytest.fixture
def auth_header(registered_user):
    return {"Authorization": f"Bearer {registered_user['access_token']}"}


@pytest.fixture
def alert_id(client, auth_header):
    """Create an alert and return its ID."""
    resp = client.post(
        "/api/ingest/alerts",
        json={
            "source": "prometheus",
            "alert_type": "cpu_threshold",
            "title": "CPU usage > 90%",
            "description": "prod-api-01 cpu at 94%",
            "severity": "SEV2",
        },
        headers=auth_header,
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def random_log_message():
    words = ["ERROR", "timeout", "connection", "refused", "database", "crash", "memory", "overflow",
             "disk", "full", "permission", "denied", "not", "found", "unexpected", "response",
             "authentication", "failed", "rate", "limit", "exceeded", "service", "unavailable",
             "internal", "server", "bad", "gateway", "DNS", "resolution", "SSL", "handshake"]
    return " ".join(random.choices(words, k=random.randint(3, 8)))


class TestLogIngestion:
    """POST /api/ingest/logs — bulk ingest up to 1000 entries."""

    def test_ingest_single(self, client, auth_header):
        resp = client.post(
            "/api/ingest/logs",
            json={"entries": [{"service": "api-gateway", "level": "info", "message": "request completed"}]},
            headers=auth_header,
        )
        assert resp.status_code == 202, resp.text
        data = resp.json()
        assert data["accepted"] == 1
        assert data["entries"][0]["service"] == "api-gateway"
        assert data["entries"][0]["level"] == "info"
        assert "id" in data["entries"][0]

    def test_ingest_bulk_100(self, client, auth_header):
        entries = [
            {"service": "auth-service", "level": "warn", "message": random_log_message()}
            for _ in range(100)
        ]
        resp = client.post(
            "/api/ingest/logs",
            json={"entries": entries},
            headers=auth_header,
        )
        assert resp.status_code == 202, resp.text
        assert resp.json()["accepted"] == 100

    def test_ingest_exceeds_limit(self, client, auth_header):
        entries = [
            {"service": "svc", "level": "info", "message": "x" * 10}
            for _ in range(1001)
        ]
        resp = client.post(
            "/api/ingest/logs",
            json={"entries": entries},
            headers=auth_header,
        )
        assert resp.status_code == 422, resp.text

    def test_ingest_malformed_entry(self, client, auth_header):
        resp = client.post(
            "/api/ingest/logs",
            json={"entries": [{"service": "", "level": "info", "message": ""}]},
            headers=auth_header,
        )
        assert resp.status_code == 422, resp.text
        detail = resp.json().get("detail", "")
        assert len(detail) > 0

    def test_ingest_unauthorized(self, client):
        resp = client.post(
            "/api/ingest/logs",
            json={"entries": [{"service": "svc", "level": "info", "message": "test"}]},
        )
        assert resp.status_code in (401, 403), resp.text


class TestLogSearch:
    """GET /api/logs/search — full-text search with filters."""

    @pytest.fixture(scope="class", autouse=True)
    def seed_10k_logs(self, client, registered_user):
        """Seed 10 000 log entries for search timing tests."""
        auth_header = {"Authorization": f"Bearer {registered_user['access_token']}"}
        services = ["api-gateway", "auth-service", "db-worker", "cache-layer", "frontend-srv"]
        levels = ["debug", "info", "warn", "error", "fatal"]

        BATCH_SIZE = 500
        total = 0
        for batch_start in range(0, 10000, BATCH_SIZE):
            entries = []
            for i in range(BATCH_SIZE):
                svc = random.choice(services)
                lvl = random.choice(levels)
                msg = random_log_message()
                entries.append({"service": svc, "level": lvl, "message": msg})
            resp = client.post("/api/ingest/logs", json={"entries": entries}, headers=auth_header)
            assert resp.status_code == 202
            total += resp.json()["accepted"]
        assert total == 10000

    def test_search_by_query(self, client, registered_user):
        auth_header = {"Authorization": f"Bearer {registered_user['access_token']}"}
        resp = client.get(
            "/api/logs/search",
            params={"q": "timeout", "per_page": 10},
            headers=auth_header,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert len(data["data"]) <= 10
        assert data["pagination"]["total"] >= 0
        assert data["pagination"]["page"] == 1

    def test_search_by_service_and_level(self, client, registered_user):
        auth_header = {"Authorization": f"Bearer {registered_user['access_token']}"}
        resp = client.get(
            "/api/logs/search",
            params={"service": "api-gateway", "level": "error", "per_page": 20},
            headers=auth_header,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        for entry in data["data"]:
            assert entry["service"] == "api-gateway"
            assert entry["level"] == "error"

    def test_search_timing_under_500ms(self, client, registered_user):
        """Search timing assertion < 500ms on 10k rows (FM-09)."""
        auth_header = {"Authorization": f"Bearer {registered_user['access_token']}"}
        t0 = time.monotonic()
        resp = client.get(
            "/api/logs/search",
            params={"q": "database error", "per_page": 50},
            headers=auth_header,
        )
        elapsed = time.monotonic() - t0
        assert resp.status_code == 200, resp.text
        assert elapsed < 0.5, f"Search took {elapsed:.3f}s, expected < 0.5s"

    def test_search_pagination(self, client, registered_user):
        auth_header = {"Authorization": f"Bearer {registered_user['access_token']}"}
        resp = client.get(
            "/api/logs/search",
            params={"page": 2, "per_page": 10},
            headers=auth_header,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["pagination"]["page"] == 2
        assert data["pagination"]["per_page"] == 10
        assert data["pagination"]["total_pages"] >= 1

    def test_search_by_time_range(self, client, registered_user):
        auth_header = {"Authorization": f"Bearer {registered_user['access_token']}"}
        now = datetime.now(timezone.utc)
        from_ts = (now - timedelta(hours=1)).isoformat()
        to_ts = now.isoformat()
        resp = client.get(
            "/api/logs/search",
            params={"from": from_ts, "to": to_ts, "per_page": 5},
            headers=auth_header,
        )
        assert resp.status_code == 200, resp.text

    def test_search_unauthorized(self, client):
        resp = client.get("/api/logs/search", params={"q": "test"})
        assert resp.status_code in (401, 403), resp.text


class TestAlertCRUD:
    """Alert lifecycle: create, list, resolve."""

    def test_create_alert(self, client, auth_header):
        resp = client.post(
            "/api/ingest/alerts",
            json={
                "source": "prometheus",
                "alert_type": "cpu_threshold",
                "title": "CPU usage > 90%",
                "description": "prod-api-01 cpu at 94%",
                "severity": "SEV2",
            },
            headers=auth_header,
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["title"] == "CPU usage > 90%"
        assert data["source"] == "prometheus"
        assert data["severity"] == "SEV2"
        assert data["is_resolved"] is False
        assert "id" in data

    def test_create_alert_minimal(self, client, auth_header):
        resp = client.post(
            "/api/ingest/alerts",
            json={
                "source": "grafana",
                "alert_type": "memory",
                "title": "Memory alert",
            },
            headers=auth_header,
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["severity"] == "SEV3"

    def test_list_alerts(self, client, auth_header):
        # Create two alerts first
        client.post(
            "/api/ingest/alerts",
            json={"source": "src1", "alert_type": "t1", "title": "Alert 1"},
            headers=auth_header,
        )
        client.post(
            "/api/ingest/alerts",
            json={"source": "src2", "alert_type": "t2", "title": "Alert 2"},
            headers=auth_header,
        )
        resp = client.get("/api/alerts", headers=auth_header)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_list_alerts_filter_resolved(self, client, auth_header, alert_id):
        resp = client.get("/api/alerts", params={"is_resolved": False}, headers=auth_header)
        assert resp.status_code == 200, resp.text
        for alert in resp.json():
            assert alert["is_resolved"] is False

    def test_resolve_alert(self, client, auth_header, alert_id, registered_user):
        resp = client.post(f"/api/alerts/{alert_id}/resolve", headers=auth_header)
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["is_resolved"] is True
        assert data["resolved_at"] is not None
        assert data["resolved_by"] == registered_user["user_id"]

    def test_resolve_already_resolved(self, client, auth_header, alert_id):
        client.post(f"/api/alerts/{alert_id}/resolve", headers=auth_header)
        resp = client.post(f"/api/alerts/{alert_id}/resolve", headers=auth_header)
        assert resp.status_code == 409, resp.text

    def test_resolve_nonexistent(self, client, auth_header):
        resp = client.post(
            "/api/alerts/00000000-0000-0000-0000-000000000000/resolve",
            headers=auth_header,
        )
        assert resp.status_code == 404, resp.text

    def test_alert_unauthorized(self, client):
        resp = client.get("/api/alerts")
        assert resp.status_code in (401, 403)
