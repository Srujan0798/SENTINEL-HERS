import pytest
from uuid import uuid4
from fastapi import FastAPI, Depends, status
from fastapi.testclient import TestClient

from src.backend.auth.dependencies import get_current_user_dependency
from src.backend.rbac.models import Role, UserContext
from src.backend.rbac.dependencies import require_role, require_permission


def make_user_dict(role: Role) -> dict:
    return {
        "id": str(uuid4()),
        "team_id": str(uuid4()),
        "role": role.value,
        "email": f"{role.value}@test.com",
        "is_active": True,
    }


OWNER = make_user_dict(Role.OWNER)
RESPONDER = make_user_dict(Role.RESPONDER)
VIEWER = make_user_dict(Role.VIEWER)


def create_app(current_user: dict) -> FastAPI:
    app = FastAPI()

    async def mock_get_current_user() -> dict:
        return current_user

    app.dependency_overrides[get_current_user_dependency] = mock_get_current_user

    @app.get("/read-route")
    async def read_route(user: UserContext = Depends(require_role(Role.OWNER, Role.RESPONDER, Role.VIEWER))):
        return {"role": user.role.value, "access": "granted"}

    @app.post("/incidents/triage")
    async def triage_route(user: UserContext = Depends(require_role(Role.OWNER, Role.RESPONDER))):
        return {"role": user.role.value, "action": "triage", "access": "granted"}

    @app.post("/incidents/create")
    async def create_incident(user: UserContext = Depends(require_role(Role.OWNER, Role.RESPONDER))):
        return {"role": user.role.value, "action": "create_incident", "access": "granted"}

    @app.post("/incidents/assign")
    async def assign_incident(user: UserContext = Depends(require_role(Role.OWNER, Role.RESPONDER))):
        return {"role": user.role.value, "action": "assign", "access": "granted"}

    @app.post("/incidents/resolve")
    async def resolve_incident(user: UserContext = Depends(require_role(Role.OWNER, Role.RESPONDER))):
        return {"role": user.role.value, "action": "resolve", "access": "granted"}

    @app.post("/incidents/comment")
    async def comment_incident(user: UserContext = Depends(require_role(Role.OWNER, Role.RESPONDER))):
        return {"role": user.role.value, "action": "comment", "access": "granted"}

    @app.delete("/incidents/{incident_id}")
    async def delete_incident(incident_id: str, user: UserContext = Depends(require_role(Role.OWNER))):
        return {"role": user.role.value, "action": "delete", "incident_id": incident_id, "access": "granted"}

    @app.post("/incidents/{incident_id}/escalate")
    async def escalate_incident(incident_id: str, user: UserContext = Depends(require_role(Role.OWNER))):
        return {"role": user.role.value, "action": "escalate", "incident_id": incident_id, "access": "granted"}

    return app


class TestViewerPermissions:
    def test_viewer_can_read(self):
        app = create_app(VIEWER)
        client = TestClient(app)
        response = client.get("/read-route")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["role"] == "viewer"

    def test_viewer_gets_403_on_triage(self):
        app = create_app(VIEWER)
        client = TestClient(app)
        response = client.post("/incidents/triage")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_viewer_gets_403_on_create(self):
        app = create_app(VIEWER)
        client = TestClient(app)
        response = client.post("/incidents/create")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_viewer_gets_403_on_assign(self):
        app = create_app(VIEWER)
        client = TestClient(app)
        response = client.post("/incidents/assign")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_viewer_gets_403_on_resolve(self):
        app = create_app(VIEWER)
        client = TestClient(app)
        response = client.post("/incidents/resolve")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_viewer_gets_403_on_comment(self):
        app = create_app(VIEWER)
        client = TestClient(app)
        response = client.post("/incidents/comment")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_viewer_gets_403_on_delete(self):
        app = create_app(VIEWER)
        client = TestClient(app)
        response = client.delete(f"/incidents/{uuid4()}")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_viewer_gets_403_on_escalate(self):
        app = create_app(VIEWER)
        client = TestClient(app)
        response = client.post(f"/incidents/{uuid4()}/escalate")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestResponderPermissions:
    def test_responder_can_read(self):
        app = create_app(RESPONDER)
        client = TestClient(app)
        response = client.get("/read-route")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["role"] == "responder"

    def test_responder_can_triage(self):
        app = create_app(RESPONDER)
        client = TestClient(app)
        response = client.post("/incidents/triage")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["action"] == "triage"

    def test_responder_can_create(self):
        app = create_app(RESPONDER)
        client = TestClient(app)
        response = client.post("/incidents/create")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["action"] == "create_incident"

    def test_responder_can_assign(self):
        app = create_app(RESPONDER)
        client = TestClient(app)
        response = client.post("/incidents/assign")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["action"] == "assign"

    def test_responder_can_resolve(self):
        app = create_app(RESPONDER)
        client = TestClient(app)
        response = client.post("/incidents/resolve")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["action"] == "resolve"

    def test_responder_can_comment(self):
        app = create_app(RESPONDER)
        client = TestClient(app)
        response = client.post("/incidents/comment")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["action"] == "comment"

    def test_responder_gets_403_on_delete(self):
        app = create_app(RESPONDER)
        client = TestClient(app)
        response = client.delete(f"/incidents/{uuid4()}")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_responder_gets_403_on_escalate(self):
        app = create_app(RESPONDER)
        client = TestClient(app)
        response = client.post(f"/incidents/{uuid4()}/escalate")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestOwnerPermissions:
    def test_owner_can_read(self):
        app = create_app(OWNER)
        client = TestClient(app)
        response = client.get("/read-route")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["role"] == "owner"

    def test_owner_can_triage(self):
        app = create_app(OWNER)
        client = TestClient(app)
        response = client.post("/incidents/triage")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["action"] == "triage"

    def test_owner_can_create(self):
        app = create_app(OWNER)
        client = TestClient(app)
        response = client.post("/incidents/create")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["action"] == "create_incident"

    def test_owner_can_assign(self):
        app = create_app(OWNER)
        client = TestClient(app)
        response = client.post("/incidents/assign")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["action"] == "assign"

    def test_owner_can_resolve(self):
        app = create_app(OWNER)
        client = TestClient(app)
        response = client.post("/incidents/resolve")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["action"] == "resolve"

    def test_owner_can_comment(self):
        app = create_app(OWNER)
        client = TestClient(app)
        response = client.post("/incidents/comment")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["action"] == "comment"

    def test_owner_can_delete(self):
        app = create_app(OWNER)
        client = TestClient(app)
        response = client.delete(f"/incidents/{uuid4()}")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["action"] == "delete"

    def test_owner_can_escalate(self):
        app = create_app(OWNER)
        client = TestClient(app)
        response = client.post(f"/incidents/{uuid4()}/escalate")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["action"] == "escalate"
