"""Integration tests for per-incident comms — channels, messages, mentions, AI, realtime."""
import asyncio
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_comms.db")
os.environ.setdefault("JWT_SECRET", "test-secret-key-long-enough-32ch!!")
os.environ.setdefault("JWT_REFRESH_SECRET", "test-refresh-long-enough-32ch!!")
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("AI_PROVIDER", "mock")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import ORM models so Base.metadata knows all tables.
import src.backend.shared_models  # noqa
import src.backend.comms.models  # noqa
from src.backend.incidents import models as _im  # noqa
from src.backend.logs import models as _lm  # noqa
from src.backend.tasks import models as _tm  # noqa
from src.backend.db import Base, get_db

# Importing the comms package installs the lifecycle hook on IncidentService.
import src.backend.comms  # noqa: F401  — installs auto-channel hook

from api.main import app

# Make sure the comms router is wired in (other tests do this too).
from src.backend.comms.routes import router as comms_router  # noqa

app.include_router(comms_router)

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_comms.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
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
    Path("test_comms.db").unlink(missing_ok=True)


@pytest.fixture
def auth():
    _email_counter[0] += 1
    n = _email_counter[0]
    email = f"comms{n}@sentinel.io"
    name = f"Comms Tester{n}"
    resp = client.post(
        "/auth/register",
        json={
            "email": email,
            "password": "testpassword123",
            "name": name,
            "team_name": f"Comms Team {n}",
        },
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    return {
        "headers": {"Authorization": f"Bearer {data['access_token']}"},
        "team_id": data["user"]["team_id"],
        "user_id": data["user"]["id"],
        "name": name,
        "email": email,
    }


@pytest.fixture
def incident_id(auth):
    resp = client.post(
        "/api/incidents",
        json={"title": "Comms Test Incident", "severity": "SEV2"},
        headers=auth["headers"],
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


class TestChannelAutoCreation:
    def test_channel_auto_created_with_incident(self, auth, incident_id):
        """Channel must exist immediately after the incident is created."""
        resp = client.get(
            f"/api/incidents/{incident_id}/channel",
            headers=auth["headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["incident_id"] == incident_id
        assert data["team_id"] == auth["team_id"]
        assert data["name"].startswith("#")
        assert data["is_archived"] is False
        assert data["message_count"] == 0

    def test_get_channel_idempotent(self, auth, incident_id):
        """Calling get-channel twice returns the same channel id."""
        a = client.get(
            f"/api/incidents/{incident_id}/channel", headers=auth["headers"]
        ).json()
        b = client.get(
            f"/api/incidents/{incident_id}/channel", headers=auth["headers"]
        ).json()
        assert a["id"] == b["id"]
        assert a["incident_id"] == b["incident_id"]

    def test_get_channel_404_for_unknown_incident(self, auth):
        resp = client.get(
            "/api/incidents/00000000-0000-0000-0000-999999999999/channel",
            headers=auth["headers"],
        )
        assert resp.status_code == 404


class TestMessages:
    def test_post_user_message(self, auth, incident_id):
        resp = client.post(
            f"/api/incidents/{incident_id}/messages",
            json={"body": "Investigating DB connection pool", "author_type": "user"},
            headers=auth["headers"],
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["body"] == "Investigating DB connection pool"
        assert data["author_type"] == "user"
        assert data["author_id"] == auth["user_id"]
        assert data["author_name"] == auth["name"]
        assert data["incident_id"] == incident_id

    def test_post_ai_message(self, auth, incident_id):
        resp = client.post(
            f"/api/incidents/{incident_id}/messages",
            json={
                "body": "AI summary: root cause is connection pool exhaustion",
                "author_type": "ai",
                "metadata": {"source": "ai_summary", "confidence": 0.92},
            },
            headers=auth["headers"],
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["author_type"] == "ai"
        assert data["metadata"]["source"] == "ai_summary"
        assert data["metadata"]["confidence"] == 0.92

    def test_post_message_strips_whitespace(self, auth, incident_id):
        resp = client.post(
            f"/api/incidents/{incident_id}/messages",
            json={"body": "   hello   ", "author_type": "user"},
            headers=auth["headers"],
        )
        assert resp.status_code == 201
        assert resp.json()["body"] == "hello"

    def test_post_message_rejects_empty(self, auth, incident_id):
        resp = client.post(
            f"/api/incidents/{incident_id}/messages",
            json={"body": "   ", "author_type": "user"},
            headers=auth["headers"],
        )
        assert resp.status_code == 400

    def test_post_message_rejects_invalid_author_type(self, auth, incident_id):
        resp = client.post(
            f"/api/incidents/{incident_id}/messages",
            json={"body": "x", "author_type": "robot"},
            headers=auth["headers"],
        )
        # 422 from pydantic pattern validator
        assert resp.status_code == 422

    def test_list_messages_empty(self, auth, incident_id):
        resp = client.get(
            f"/api/incidents/{incident_id}/messages",
            headers=auth["headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"] == []
        assert data["pagination"]["total"] == 0

    def test_list_messages_paginated(self, auth, incident_id):
        for i in range(5):
            r = client.post(
                f"/api/incidents/{incident_id}/messages",
                json={"body": f"msg {i}", "author_type": "user"},
                headers=auth["headers"],
            )
            assert r.status_code == 201
        resp = client.get(
            f"/api/incidents/{incident_id}/messages?page=1&per_page=2",
            headers=auth["headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) == 2
        assert data["pagination"]["total"] == 5
        assert data["pagination"]["total_pages"] == 3

    def test_list_messages_unauthorized(self, incident_id):
        resp = client.get(f"/api/incidents/{incident_id}/messages")
        assert resp.status_code in (401, 403)


class TestMentions:
    def test_mention_parsed_by_name(self, auth, incident_id):
        body = f"Hey @{auth['name']} can you take a look?"
        resp = client.post(
            f"/api/incidents/{incident_id}/messages",
            json={"body": body, "author_type": "user"},
            headers=auth["headers"],
        )
        assert resp.status_code == 201
        data = resp.json()
        mentions = data["mentions"]
        assert len(mentions) == 1
        assert mentions[0]["user_id"] == auth["user_id"]
        assert mentions[0]["user_name"] == auth["name"]
        assert mentions[0].get("unresolved") is False

    def test_mention_parsed_by_email_handle(self, auth, incident_id):
        # email local part is "comms1"
        handle = auth["email"].split("@")[0]
        body = f"paging @{handle} — please respond"
        resp = client.post(
            f"/api/incidents/{incident_id}/messages",
            json={"body": body, "author_type": "user"},
            headers=auth["headers"],
        )
        assert resp.status_code == 201
        data = resp.json()
        mentions = data["mentions"]
        assert len(mentions) == 1
        assert mentions[0]["user_id"] == auth["user_id"]

    def test_unknown_mention_marked_unresolved(self, auth, incident_id):
        body = "cc @nonexistentperson"
        resp = client.post(
            f"/api/incidents/{incident_id}/messages",
            json={"body": body, "author_type": "user"},
            headers=auth["headers"],
        )
        assert resp.status_code == 201
        data = resp.json()
        mentions = data["mentions"]
        assert len(mentions) == 1
        assert mentions[0].get("unresolved") is True
        assert mentions[0]["user_name"] == "nonexistentperson"

    def test_multiple_mentions_dedup(self, auth, incident_id):
        body = f"@{auth['name']} and @{auth['name']} again"
        resp = client.post(
            f"/api/incidents/{incident_id}/messages",
            json={"body": body, "author_type": "user"},
            headers=auth["headers"],
        )
        assert resp.status_code == 201
        data = resp.json()
        ids = {m["user_id"] for m in data["mentions"]}
        assert ids == {auth["user_id"]}


class TestRealtimeDelivery:
    def test_channel_message_event_published(self, auth, incident_id):
        """When a message is posted, the realtime hub must broadcast a
        `channel.message` event for the team."""
        from src.backend.realtime.hub import get_hub

        async def driver():
            hub = get_hub()
            await hub.initialize()
            entry = await hub.subscribe(auth["team_id"])
            try:
                # Post a message from a different thread (sync test client).
                import threading
                posted = {}

                def post():
                    r = client.post(
                        f"/api/incidents/{incident_id}/messages",
                        json={"body": "realtime check", "author_type": "user"},
                        headers=auth["headers"],
                    )
                    posted["resp"] = r

                t = threading.Thread(target=post)
                t.start()
                t.join(timeout=5.0)
                assert posted["resp"].status_code == 201, posted["resp"].text

                # Drain the queue for channel.message
                for _ in range(10):
                    try:
                        evt = await asyncio.wait_for(entry.queue.get(), timeout=2.0)
                    except asyncio.TimeoutError:
                        break
                    if evt.event_type == "channel.message":
                        assert evt.payload["incident_id"] == incident_id
                        assert evt.payload["body"] == "realtime check"
                        return
                raise AssertionError("channel.message event not received")
            finally:
                await hub.unsubscribe(entry)

        asyncio.run(driver())

    def test_mention_created_event_published(self, auth, incident_id):
        """Posting a message that mentions someone must emit a `mention.created`
        event scoped to the mentioned user."""
        from src.backend.realtime.hub import get_hub

        async def driver():
            hub = get_hub()
            await hub.initialize()
            entry = await hub.subscribe(auth["team_id"])
            try:
                import threading
                posted = {}

                def post():
                    r = client.post(
                        f"/api/incidents/{incident_id}/messages",
                        json={
                            "body": f"@{auth['name']} take a look",
                            "author_type": "user",
                        },
                        headers=auth["headers"],
                    )
                    posted["resp"] = r

                t = threading.Thread(target=post)
                t.start()
                t.join(timeout=5.0)
                assert posted["resp"].status_code == 201

                mention_evt = None
                channel_evt = None
                for _ in range(20):
                    try:
                        evt = await asyncio.wait_for(entry.queue.get(), timeout=2.0)
                    except asyncio.TimeoutError:
                        break
                    if evt.event_type == "mention.created" and not mention_evt:
                        mention_evt = evt
                    if evt.event_type == "channel.message" and not channel_evt:
                        channel_evt = evt
                    if mention_evt and channel_evt:
                        break

                assert channel_evt is not None, "channel.message event missing"
                assert mention_evt is not None, "mention.created event missing"
                payload = mention_evt.payload
                assert payload["mentioned_user_id"] == auth["user_id"]
                assert payload["incident_id"] == incident_id
                assert "@" in payload["preview"]
            finally:
                await hub.unsubscribe(entry)

        asyncio.run(driver())


class TestChannelMetadata:
    def test_message_count_increments(self, auth, incident_id):
        ch0 = client.get(
            f"/api/incidents/{incident_id}/channel", headers=auth["headers"]
        ).json()
        assert ch0["message_count"] == 0
        for i in range(3):
            client.post(
                f"/api/incidents/{incident_id}/messages",
                json={"body": f"hi {i}", "author_type": "user"},
                headers=auth["headers"],
            )
        ch1 = client.get(
            f"/api/incidents/{incident_id}/channel", headers=auth["headers"]
        ).json()
        assert ch1["message_count"] == 3


class TestTeamMembers:
    def test_team_members_for_mention_autocomplete(self, auth, incident_id):
        resp = client.get(
            f"/api/incidents/{incident_id}/team-members",
            headers=auth["headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        ids = {m["id"] for m in data["data"]}
        assert auth["user_id"] in ids
        me = next(m for m in data["data"] if m["id"] == auth["user_id"])
        assert me["email"] == auth["email"]
        assert me["name"] == auth["name"]


class TestAIPostedMessages:
    def test_ai_postmortem_posted_as_ai_message(self, auth, incident_id):
        """Simulate an AI service posting a postmortem to the channel."""
        body = "Postmortem: connection pool exhausted at 14:32 UTC. Mitigation: increased pool size from 50 to 200. MTTR: 8m."
        resp = client.post(
            f"/api/incidents/{incident_id}/messages",
            json={"body": body, "author_type": "ai", "metadata": {"kind": "postmortem"}},
            headers=auth["headers"],
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["author_type"] == "ai"
        assert data["metadata"]["kind"] == "postmortem"

        # List should include the AI message
        listed = client.get(
            f"/api/incidents/{incident_id}/messages", headers=auth["headers"]
        ).json()
        ai_msgs = [m for m in listed["data"] if m["author_type"] == "ai"]
        assert len(ai_msgs) >= 1
        assert any("Postmortem" in m["body"] for m in ai_msgs)


class TestCrossIncidentIsolation:
    def test_messages_isolated_per_incident(self, auth, incident_id):
        # Create a second incident
        r2 = client.post(
            "/api/incidents",
            json={"title": "Second Incident", "severity": "SEV3"},
            headers=auth["headers"],
        )
        assert r2.status_code == 201
        second_id = r2.json()["id"]

        client.post(
            f"/api/incidents/{incident_id}/messages",
            json={"body": "alpha", "author_type": "user"},
            headers=auth["headers"],
        )
        client.post(
            f"/api/incidents/{second_id}/messages",
            json={"body": "beta", "author_type": "user"},
            headers=auth["headers"],
        )

        a = client.get(
            f"/api/incidents/{incident_id}/messages", headers=auth["headers"]
        ).json()
        b = client.get(
            f"/api/incidents/{second_id}/messages", headers=auth["headers"]
        ).json()
        assert any(m["body"] == "alpha" for m in a["data"])
        assert not any(m["body"] == "beta" for m in a["data"])
        assert any(m["body"] == "beta" for m in b["data"])
        assert not any(m["body"] == "alpha" for m in b["data"])
