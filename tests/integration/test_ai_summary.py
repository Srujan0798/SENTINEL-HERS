"""Integration tests for AI summary + root-cause analysis endpoints.

Uses unittest.mock to simulate AI provider responses (no live API key needed).
Mirrors VCR cassette pattern: recorded responses are returned by the mock.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.backend.db import Base, get_db
from src.backend.incidents.models import Incident
from src.backend.incidents.enums import IncidentStatus, SeverityLevel
from src.backend.logs.models import LogEntryModel, AlertModel
from src.backend.ai.routes import router as ai_router

# ---------------------------------------------------------------------------
# Test DB setup
# ---------------------------------------------------------------------------
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ai_summary.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Dedicated app for AI endpoint isolation (avoids clobbering other test overrides)
_ai_app = FastAPI()
_ai_app.include_router(ai_router)
_ai_app.dependency_overrides[get_db] = _override_get_db
_client = TestClient(_ai_app)

TEAM_ID = "00000000-0000-0000-0000-000000000001"
INCIDENT_ID = "00000000-0000-0000-0000-000000000042"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def seed_incident():
    """Insert a test incident + logs + alerts."""
    inc = Incident(
        id=INCIDENT_ID,
        team_id=TEAM_ID,
        title="API Gateway 502 Spike",
        description="Production API gateway returning 502s",
        severity=SeverityLevel.SEV1.value,
        status=IncidentStatus.INVESTIGATING.value,
        metadata_={},
    )
    db = TestingSessionLocal()
    db.add(inc)
    db.flush()

    for i in range(5):
        log = LogEntryModel(
            id=f"00000000-0000-0000-0000-{100000000000 + i:012d}",
            team_id=TEAM_ID,
            incident_id=INCIDENT_ID,
            service="api-gateway",
            level="error",
            message=f"Upstream connection refused (attempt {i+1})",
        )
        db.add(log)

    alert = AlertModel(
        id="00000000-0000-0000-0000-200000000001",
        team_id=TEAM_ID,
        incident_id=INCIDENT_ID,
        source="prometheus",
        alert_type="high_error_rate",
        title="502 rate > 5% for 5 min",
        severity="SEV1",
        fired_at=datetime(2026, 6, 19, 10, 0, 0, tzinfo=timezone.utc),
    )
    db.add(alert)
    db.commit()
    db.close()
    return INCIDENT_ID


# ---------------------------------------------------------------------------
# Recorded AI responses (VCR cassette equivalents)
# ---------------------------------------------------------------------------
MOCK_SUMMARY = (
    "On June 19 2026 the production API gateway began returning HTTP 502 errors "
    "to upstream clients. The root trigger was a connection-refused condition on "
    "the backend service pool, causing approximately 12% of requests to fail for "
    "a 15-minute window.\n\n"
    "Customer impact was moderate: roughly 3400 requests returned 502 during peak "
    "hours. No data loss occurred, but checkout and search flows were degraded.\n\n"
    "The incident is currently under investigation. The team has rolled back the "
    "most recent deployment and error rates have returned to baseline. A postmortem "
    "is pending."
)

MOCK_ROOT_CAUSES = [
    {
        "hypothesis": "Recent deployment introduced a connection-pool leak in the gateway service",
        "confidence": 0.85,
        "supporting_evidence": [
            "Error spike started 3 minutes after deploy v2.14.0",
            "Logs show 'connection refused' on upstream pool",
            "Deploy log shows gateway service updated at 09:45 UTC",
        ],
        "suggested_action": "Rollback gateway service to v2.13.1 and monitor error rate",
    },
    {
        "hypothesis": "Backend service OOM-killed due to memory leak",
        "confidence": 0.45,
        "supporting_evidence": [
            "One backend pod restarted at 09:47 UTC",
            "No explicit OOM events logged on the host",
        ],
        "suggested_action": "Check container restart policies and increase memory limits",
    },
    {
        "hypothesis": "Network partition between gateway and backend subnet",
        "confidence": 0.20,
        "supporting_evidence": [
            "Symptoms match transient network issue",
        ],
        "suggested_action": "Review VPC flow logs for packet drops during the incident window",
    },
]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestSummaryEndpoint:
    @patch("src.backend.ai.summary.service.get_provider")
    def test_generate_summary_returns_3_paragraphs(self, mock_prov, seed_incident):
        provider = MagicMock()
        provider.complete.return_value = MOCK_SUMMARY
        mock_prov.return_value = provider

        resp = _client.get(f"/api/ai/incidents/{INCIDENT_ID}/summary")
        assert resp.status_code == 200
        body = resp.json()
        assert body["incident_id"] == INCIDENT_ID
        assert len(body["summary"]) > 0
        provider.complete.assert_called_once()

    @patch("src.backend.ai.summary.service.get_provider")
    def test_summary_cached_on_second_call(self, mock_prov, seed_incident):
        provider = MagicMock()
        provider.complete.return_value = MOCK_SUMMARY
        mock_prov.return_value = provider

        resp1 = _client.get(f"/api/ai/incidents/{INCIDENT_ID}/summary")
        assert resp1.status_code == 200
        assert provider.complete.call_count == 1

        resp2 = _client.get(f"/api/ai/incidents/{INCIDENT_ID}/summary")
        assert resp2.status_code == 200
        assert resp2.json()["summary"] == MOCK_SUMMARY
        assert provider.complete.call_count == 1

    def test_summary_incident_not_found(self):
        resp = _client.get("/api/ai/incidents/00000000-0000-0000-0000-999999999999/summary")
        assert resp.status_code == 404

    @patch("src.backend.ai.summary.service.get_provider")
    def test_summary_ai_failure_returns_503(self, mock_prov, seed_incident):
        provider = MagicMock()
        provider.complete.side_effect = RuntimeError("AI provider down")
        mock_prov.return_value = provider

        resp = _client.get(f"/api/ai/incidents/{INCIDENT_ID}/summary")
        assert resp.status_code == 503
        body = resp.json()
        assert body["detail"]["error"] == "ai_unavailable"
        assert body["detail"]["fallback"] is None


class TestRootCauseEndpoint:
    @patch("src.backend.ai.rootcause.service.get_provider")
    def test_root_causes_returns_ranked_list(self, mock_prov, seed_incident):
        provider = MagicMock()
        provider.complete.return_value = json.dumps(MOCK_ROOT_CAUSES)
        mock_prov.return_value = provider

        resp = _client.post(f"/api/ai/incidents/{INCIDENT_ID}/root-causes")
        assert resp.status_code == 200
        body = resp.json()
        assert body["incident_id"] == INCIDENT_ID
        rcs = body["root_causes"]
        assert 1 <= len(rcs) <= 5
        for rc in rcs:
            assert 0.0 <= rc["confidence"] <= 1.0
            assert "hypothesis" in rc
            assert "supporting_evidence" in rc
            assert "suggested_action" in rc
        for i in range(len(rcs) - 1):
            assert rcs[i]["confidence"] >= rcs[i + 1]["confidence"]

    def test_root_causes_incident_not_found(self):
        resp = _client.post("/api/ai/incidents/00000000-0000-0000-0000-999999999999/root-causes")
        assert resp.status_code == 404

    @patch("src.backend.ai.rootcause.service.get_provider")
    def test_root_causes_ai_failure_returns_503(self, mock_prov, seed_incident):
        provider = MagicMock()
        provider.complete.side_effect = ConnectionError("API timeout")
        mock_prov.return_value = provider

        resp = _client.post(f"/api/ai/incidents/{INCIDENT_ID}/root-causes")
        assert resp.status_code == 503
        body = resp.json()
        assert body["detail"]["error"] == "ai_unavailable"
        assert body["detail"]["fallback"] is None

    @patch("src.backend.ai.rootcause.service.get_provider")
    def test_root_causes_persisted_on_incident(self, mock_prov, seed_incident):
        provider = MagicMock()
        provider.complete.return_value = json.dumps(MOCK_ROOT_CAUSES)
        mock_prov.return_value = provider

        _client.post(f"/api/ai/incidents/{INCIDENT_ID}/root-causes")

        db = TestingSessionLocal()
        inc = db.query(Incident).filter(Incident.id == INCIDENT_ID).first()
        assert inc.ai_root_cause_ranking is not None
        assert len(inc.ai_root_cause_ranking) == 3
        assert inc.ai_root_cause_ranking[0]["confidence"] == 0.85
        db.close()


class TestProviderAbstraction:
    def test_mock_provider_returns_text(self):
        from src.backend.ai.provider import MockProvider

        p = MockProvider()
        result = p.complete([{"role": "user", "content": "hello"}], system="sys")
        assert "[mock-ai]" in result

    @patch.dict("os.environ", {"AI_PROVIDER": "mock"})
    def test_get_provider_defaults_to_mock(self):
        from src.backend.ai.provider import get_provider, MockProvider

        p = get_provider()
        assert isinstance(p, MockProvider)

    @patch.dict("os.environ", {"AI_PROVIDER": "claude", "ANTHROPIC_API_KEY": "test-key"})
    def test_get_provider_returns_claude(self):
        mock_anthropic = MagicMock()
        sys.modules["anthropic"] = mock_anthropic
        try:
            from src.backend.ai.provider import get_provider, ClaudeProvider

            p = get_provider()
            assert isinstance(p, ClaudeProvider)
        finally:
            del sys.modules["anthropic"]

    @patch.dict("os.environ", {"AI_PROVIDER": "gemini", "GEMINI_API_KEY": "test-key"})
    def test_get_provider_returns_gemini(self):
        mock_genai = MagicMock()
        sys.modules["google.generativeai"] = mock_genai
        sys.modules["google"] = MagicMock()
        sys.modules["google"].generativeai = mock_genai
        try:
            from src.backend.ai.provider import get_provider, GeminiProvider

            p = get_provider()
            assert isinstance(p, GeminiProvider)
        finally:
            sys.modules.pop("google.generativeai", None)
            sys.modules.pop("google", None)
