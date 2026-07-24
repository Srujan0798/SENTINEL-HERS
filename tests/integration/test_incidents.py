import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.backend.auth.dependencies import get_current_user_dependency
from src.backend.incidents.database import Base, get_db
from src.backend.incidents.models import Incident, TimelineEvent
from src.backend.incidents.enums import IncidentStatus, SeverityLevel
from api.main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_incidents.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


client = TestClient(app)

TEAM_ID = "00000000-0000-0000-0000-000000000001"
USER_ID = "00000000-0000-0000-0000-000000000099"


@pytest.fixture(autouse=True, scope="module")
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    yield
    app.dependency_overrides.pop(get_db, None)

@pytest.fixture(autouse=True, scope="module")
def override_auth():
    async def fake_user():
        return {"user_id": USER_ID, "team_id": TEAM_ID, "role_id": "00000000-0000-0000-0000-000000000001"}
    app.dependency_overrides[get_current_user_dependency] = fake_user
    yield
    app.dependency_overrides.pop(get_current_user_dependency, None)

@pytest.fixture(autouse=True)
def clean_tables():
    """Clean data between tests so each test starts fresh."""
    yield
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM timeline_events"))
        conn.execute(text("DELETE FROM incidents"))
        conn.commit()


def test_create_incident():
    response = client.post(
        "/api/incidents",
        json={"title": "Test Incident", "severity": "SEV2", "description": "Something broke"},
        params={"team_id": TEAM_ID, "actor": "tester"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Incident"
    assert data["severity"] == "SEV2"
    assert data["status"] == "detected"
    assert data["team_id"] == TEAM_ID


def test_list_incidents():
    client.post(
        "/api/incidents",
        json={"title": "Incident A", "severity": "SEV1"},
        params={"team_id": TEAM_ID},
    )
    client.post(
        "/api/incidents",
        json={"title": "Incident B", "severity": "SEV3"},
        params={"team_id": TEAM_ID},
    )
    response = client.get("/api/incidents", params={"team_id": TEAM_ID})
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 2
    assert data["pagination"]["total"] == 2


def test_list_incidents_filter_severity():
    client.post("/api/incidents", json={"title": "SEV1", "severity": "SEV1"}, params={"team_id": TEAM_ID})
    client.post("/api/incidents", json={"title": "SEV4", "severity": "SEV4"}, params={"team_id": TEAM_ID})
    response = client.get("/api/incidents", params={"team_id": TEAM_ID, "severity": "SEV1"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["severity"] == "SEV1"


def test_get_incident():
    create_resp = client.post(
        "/api/incidents",
        json={"title": "Fetch Me", "severity": "SEV3"},
        params={"team_id": TEAM_ID},
    )
    inc_id = create_resp.json()["id"]
    response = client.get(f"/api/incidents/{inc_id}", params={"team_id": TEAM_ID})
    assert response.status_code == 200
    assert response.json()["id"] == inc_id
    assert response.json()["title"] == "Fetch Me"


def test_get_incident_not_found():
    response = client.get(
        "/api/incidents/00000000-0000-0000-0000-999999999999",
        params={"team_id": TEAM_ID},
    )
    assert response.status_code == 404


def test_triage_state_machine_full_cycle():
    create_resp = client.post(
        "/api/incidents",
        json={"title": "State Machine Test", "severity": "SEV1"},
        params={"team_id": TEAM_ID, "actor": "commander"},
    )
    inc_id = create_resp.json()["id"]

    transitions = [
        ("triaging", "triaging"),
        ("investigating", "investigating"),
        ("mitigating", "mitigating"),
        ("resolved", "resolved"),
        ("closed", "closed"),
    ]

    for status_val, expected in transitions:
        resp = client.patch(
            f"/api/incidents/{inc_id}",
            json={"status": status_val},
            params={"team_id": TEAM_ID, "actor": "commander"},
        )
        assert resp.status_code == 200, f"Transition to {status_val} failed: {resp.text}"
        assert resp.json()["status"] == expected


def test_invalid_state_transition():
    create_resp = client.post(
        "/api/incidents",
        json={"title": "Bad Transition", "severity": "SEV2"},
        params={"team_id": TEAM_ID},
    )
    inc_id = create_resp.json()["id"]

    resp = client.patch(
        f"/api/incidents/{inc_id}",
        json={"status": "resolved"},
        params={"team_id": TEAM_ID},
    )
    assert resp.status_code == 422
    assert "Cannot transition" in resp.json()["detail"]


def test_invalid_transition_from_closed():
    create_resp = client.post(
        "/api/incidents",
        json={"title": "Closed Incident", "severity": "SEV3"},
        params={"team_id": TEAM_ID},
    )
    inc_id = create_resp.json()["id"]

    for s in ["triaging", "investigating", "mitigating", "resolved", "closed"]:
        client.patch(f"/api/incidents/{inc_id}", json={"status": s}, params={"team_id": TEAM_ID})

    resp = client.patch(
        f"/api/incidents/{inc_id}",
        json={"status": "triaging"},
        params={"team_id": TEAM_ID},
    )
    assert resp.status_code == 422


def test_assign_incident():
    create_resp = client.post(
        "/api/incidents",
        json={"title": "Assign Me", "severity": "SEV2"},
        params={"team_id": TEAM_ID},
    )
    inc_id = create_resp.json()["id"]

    resp = client.post(
        f"/api/incidents/{inc_id}/assign",
        json={"user_id": USER_ID},
        params={"team_id": TEAM_ID, "actor": "lead"},
    )
    assert resp.status_code == 200
    assert resp.json()["assigned_to"] == USER_ID


def test_assign_incident_not_found():
    resp = client.post(
        "/api/incidents/00000000-0000-0000-0000-999999999999/assign",
        json={"user_id": USER_ID},
        params={"team_id": TEAM_ID},
    )
    assert resp.status_code == 404


def test_timeline_events_created_on_transitions():
    create_resp = client.post(
        "/api/incidents",
        json={"title": "Timeline Test", "severity": "SEV1"},
        params={"team_id": TEAM_ID, "actor": "creator"},
    )
    inc_id = create_resp.json()["id"]

    client.patch(
        f"/api/incidents/{inc_id}",
        json={"status": "triaging"},
        params={"team_id": TEAM_ID, "actor": "responder"},
    )

    resp = client.get(f"/api/incidents/{inc_id}/timeline", params={"team_id": TEAM_ID})
    assert resp.status_code == 200
    events = resp.json()["data"]
    assert len(events) >= 2
    event_types = [e["event_type"] for e in events]
    assert "incident.created" in event_types
    assert "status.changed" in event_types


def test_timeline_provenance_columns():
    create_resp = client.post(
        "/api/incidents",
        json={"title": "Provenance Test", "severity": "SEV3"},
        params={"team_id": TEAM_ID, "actor": "engineer"},
    )
    inc_id = create_resp.json()["id"]

    resp = client.get(f"/api/incidents/{inc_id}/timeline", params={"team_id": TEAM_ID})
    assert resp.status_code == 200
    events = resp.json()["data"]
    assert len(events) >= 1
    ev = events[0]
    assert ev["source"] == "api"
    assert ev["actor"] == "engineer"
    assert ev["ts"] is not None


def test_update_incident_fields():
    create_resp = client.post(
        "/api/incidents",
        json={"title": "Original Title", "severity": "SEV3"},
        params={"team_id": TEAM_ID},
    )
    inc_id = create_resp.json()["id"]

    resp = client.patch(
        f"/api/incidents/{inc_id}",
        json={"title": "Updated Title", "severity": "SEV1", "description": "New desc"},
        params={"team_id": TEAM_ID},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Updated Title"
    assert data["severity"] == "SEV1"
    assert data["description"] == "New desc"


def test_skip_triage_direct_investigating():
    create_resp = client.post(
        "/api/incidents",
        json={"title": "Skip Test", "severity": "SEV2"},
        params={"team_id": TEAM_ID},
    )
    inc_id = create_resp.json()["id"]

    resp = client.patch(
        f"/api/incidents/{inc_id}",
        json={"status": "investigating"},
        params={"team_id": TEAM_ID},
    )
    assert resp.status_code == 422
    assert "Cannot transition" in resp.json()["detail"]
