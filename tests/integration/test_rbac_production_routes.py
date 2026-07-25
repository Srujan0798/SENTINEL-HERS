"""RBAC on real production routers (not toy apps) — ETERNITY W1."""
from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from api.main import app
from src.backend.auth.dependencies import get_current_user_dependency

TEAM = str(uuid4())
_user = {
    "id": str(uuid4()),
    "team_id": TEAM,
    "role": "admin",
    "email": "admin@test.com",
    "is_active": True,
}


@pytest.fixture
def client():
    async def current():
        return dict(_user)

    app.dependency_overrides[get_current_user_dependency] = current
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_current_user_dependency, None)
    _user["role"] = "admin"


def _as_viewer():
    _user["role"] = "viewer"
    _user["email"] = "viewer@test.com"


def _as_admin():
    _user["role"] = "admin"
    _user["email"] = "admin@test.com"


def test_viewer_forbidden_create_incident(client):
    _as_viewer()
    r = client.post(
        "/api/incidents",
        json={"title": "Nope", "severity": "SEV3", "description": "viewer cannot create"},
    )
    assert r.status_code == 403, r.text


def test_viewer_forbidden_assign_and_task(client):
    _as_admin()
    created = client.post(
        "/api/incidents",
        json={"title": "Assignable", "severity": "SEV2", "description": "x"},
    )
    assert created.status_code == 201, created.text
    iid = created.json()["id"]

    _as_viewer()
    r = client.post(f"/api/incidents/{iid}/assign", json={"user_id": _user["id"]})
    assert r.status_code == 403, r.text

    r2 = client.post(f"/api/incidents/{iid}/tasks", json={"title": "viewer task"})
    assert r2.status_code == 403, r2.text


def test_admin_can_create_incident(client):
    _as_admin()
    r = client.post(
        "/api/incidents",
        json={"title": "Admin ok", "severity": "SEV3", "description": "allowed"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["title"] == "Admin ok"


def test_viewer_can_list_incidents(client):
    _as_admin()
    client.post(
        "/api/incidents",
        json={"title": "Listable", "severity": "SEV3", "description": "x"},
    )
    _as_viewer()
    r = client.get("/api/incidents")
    assert r.status_code == 200, r.text
