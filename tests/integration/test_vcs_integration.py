"""Integration tests for GitHub/GitLab webhook ingestion + deployment listing."""
import hashlib
import hmac
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_vcs.db")
os.environ.setdefault("JWT_SECRET", "test-secret-key-long-enough-32ch!!")
os.environ.setdefault("JWT_REFRESH_SECRET", "test-refresh-long-enough-32ch!!")
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("AI_PROVIDER", "mock")
os.environ.setdefault("GITHUB_WEBHOOK_SECRET", "test-webhook-secret")
os.environ.setdefault("GITLAB_WEBHOOK_SECRET", "test-gitlab-token")

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

engine = create_engine("sqlite:///./test_vcs.db", connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


client = TestClient(app)

GITHUB_SECRET = "test-webhook-secret"


def _github_sig(body: bytes) -> str:
    return "sha256=" + hmac.new(GITHUB_SECRET.encode(), body, hashlib.sha256).hexdigest()


@pytest.fixture(autouse=True, scope="module")
def setup_db():
    app.dependency_overrides[get_db] = override_db
    Base.metadata.create_all(bind=engine)
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    Path("test_vcs.db").unlink(missing_ok=True)


_counter = [0]

@pytest.fixture
def auth():
    _counter[0] += 1
    email = f"vcs{_counter[0]}@sentinel.io"
    resp = client.post("/auth/register", json={
        "email": email, "password": "testpassword123",
        "name": "VCS Tester", "team_name": "VCS Team",
    })
    assert resp.status_code == 201
    data = resp.json()
    return {
        "headers": {"Authorization": f"Bearer {data['access_token']}"},
        "team_id": data["user"]["team_id"],
    }


class TestGitHubWebhook:
    def test_deployment_event_creates_record(self, auth):
        payload = {
            "repository": {"name": "api-gateway"},
            "deployment": {"sha": "abc123", "ref": "v1.2.3", "environment": "production", "state": "success"},
            "sender": {"login": "deploy-bot"},
        }
        body = json.dumps(payload).encode()
        sig = _github_sig(body)

        resp = client.post(
            "/api/integrations/github/webhook",
            content=body,
            params={"team_id": auth["team_id"]},
            headers={"X-Hub-Signature-256": sig, "X-GitHub-Event": "deployment", "Content-Type": "application/json"},
        )
        assert resp.status_code == 202
        assert resp.json()["event"] == "deployment"

    def test_push_event_creates_commits(self, auth):
        payload = {
            "repository": {"name": "auth-service"},
            "ref": "refs/heads/main",
            "commits": [
                {"id": "aaa111", "message": "fix: auth bug", "author": {"name": "Alice"}},
                {"id": "bbb222", "message": "chore: update deps", "author": {"name": "Bob"}},
            ],
        }
        body = json.dumps(payload).encode()
        sig = _github_sig(body)

        resp = client.post(
            "/api/integrations/github/webhook",
            content=body,
            params={"team_id": auth["team_id"]},
            headers={"X-Hub-Signature-256": sig, "X-GitHub-Event": "push", "Content-Type": "application/json"},
        )
        assert resp.status_code == 202

    def test_invalid_signature_rejected(self):
        body = b'{"test": true}'
        resp = client.post(
            "/api/integrations/github/webhook",
            content=body,
            headers={"X-Hub-Signature-256": "sha256=invalid", "X-GitHub-Event": "push", "Content-Type": "application/json"},
        )
        assert resp.status_code == 401

    def test_unknown_event_accepted(self, auth):
        body = b'{}'
        sig = _github_sig(body)
        resp = client.post(
            "/api/integrations/github/webhook",
            content=body,
            params={"team_id": auth["team_id"]},
            headers={"X-Hub-Signature-256": sig, "X-GitHub-Event": "star", "Content-Type": "application/json"},
        )
        assert resp.status_code == 202

    def test_missing_team_rejected(self, auth):
        body = b'{}'
        sig = _github_sig(body)
        resp = client.post(
            "/api/integrations/github/webhook",
            content=body,
            headers={"X-Hub-Signature-256": sig, "X-GitHub-Event": "push", "Content-Type": "application/json"},
        )
        assert resp.status_code == 400  # team_id query param required


class TestGitLabWebhook:
    def test_push_event_accepted(self, auth):
        payload = {
            "object_kind": "push",
            "project": {"name": "frontend"},
            "ref": "refs/heads/main",
            "commits": [{"id": "ccc333", "message": "feat: new UI", "author": {"name": "Carol"}}],
        }
        body = json.dumps(payload).encode()
        resp = client.post(
            "/api/integrations/gitlab/webhook",
            content=body,
            params={"team_id": auth["team_id"]},
            headers={"X-Gitlab-Token": "test-gitlab-token", "X-Gitlab-Event": "Push Hook", "Content-Type": "application/json"},
        )
        assert resp.status_code == 202

    def test_invalid_token_rejected(self):
        resp = client.post(
            "/api/integrations/gitlab/webhook",
            content=b"{}",
            headers={"X-Gitlab-Token": "wrong", "Content-Type": "application/json"},
        )
        assert resp.status_code == 401


class TestDeploymentListing:
    def test_list_deployments(self, auth):
        # seed a deployment via webhook
        payload = {
            "repository": {"name": "my-svc"},
            "deployment": {"sha": "xyz999", "ref": "v2.0.0", "environment": "staging", "state": "success"},
            "sender": {"login": "ci"},
        }
        body = json.dumps(payload).encode()
        client.post(
            "/api/integrations/github/webhook",
            content=body,
            params={"team_id": auth["team_id"]},
            headers={"X-Hub-Signature-256": _github_sig(body), "X-GitHub-Event": "deployment", "Content-Type": "application/json"},
        )

        resp = client.get("/api/integrations/deployments", headers=auth["headers"])
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        # Webhook is now tenant-scoped to the team on the URL, so the deployment
        # the same team seeded must be visible in its listing.
        assert any(d.get("sha") == "xyz999" for d in data)

    def test_list_commits(self, auth):
        resp = client.get("/api/integrations/commits", headers=auth["headers"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_deployments_unauthorized(self):
        resp = client.get("/api/integrations/deployments")
        assert resp.status_code in (401, 403)
