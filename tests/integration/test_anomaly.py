"""Integration tests for anomaly ML detection."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_anomaly.db")
os.environ.setdefault("JWT_SECRET", "test-secret-key-long-enough-32ch!!")
os.environ.setdefault("JWT_REFRESH_SECRET", "test-refresh-long-enough-32ch!!")
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("AI_PROVIDER", "mock")
os.environ.setdefault("ANOMALY_MODEL_PATH", "/tmp/test_anomaly_model.joblib")

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

engine = create_engine("sqlite:///./test_anomaly.db", connect_args={"check_same_thread": False})
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
    Base.metadata.drop_all(bind=engine)
    Path("test_anomaly.db").unlink(missing_ok=True)
    Path("/tmp/test_anomaly_model.joblib").unlink(missing_ok=True)


@pytest.fixture
def auth():
    _ctr[0] += 1
    resp = client.post("/auth/register", json={
        "email": f"anomaly{_ctr[0]}@sentinel.io",
        "password": "testpassword123",
        "name": "ML Tester",
        "team_name": f"ML Team {_ctr[0]}",
    })
    assert resp.status_code == 201
    data = resp.json()
    return {"headers": {"Authorization": f"Bearer {data['access_token']}"}}


class TestAnomalyDetector:
    def test_normal_data_not_anomaly(self):
        from src.backend.ml.anomaly.detector import score_metric_stream
        result = score_metric_stream("api-gw", [0.4])
        assert result.is_anomaly is False
        assert 0.0 <= result.score + 1  # score is a float

    def test_anomalous_data_detected(self):
        from src.backend.ml.anomaly.detector import score_metric_stream
        result = score_metric_stream("db-worker", [0.99])
        assert result.is_anomaly is True
        assert result.score < result.threshold

    def test_empty_metrics_safe(self):
        from src.backend.ml.anomaly.detector import score_metric_stream
        result = score_metric_stream("svc", [])
        assert result.is_anomaly is False

    def test_confidence_range(self):
        from src.backend.ml.anomaly.detector import score_metric_stream
        for val in [0.1, 0.3, 0.5, 0.7, 0.95]:
            result = score_metric_stream("svc", [val])
            assert isinstance(result.score, float)
            assert isinstance(result.is_anomaly, bool)


class TestAnomalyAPI:
    def test_score_endpoint(self, auth):
        resp = client.post(
            "/api/ml/score",
            json={"service": "api-gateway", "metrics": [0.4]},
            headers=auth["headers"],
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "score" in data
        assert "is_anomaly" in data
        assert "threshold" in data
        assert data["service"] == "api-gateway"

    def test_score_anomalous(self, auth):
        resp = client.post(
            "/api/ml/score",
            json={"service": "db-worker", "metrics": [0.99]},
            headers=auth["headers"],
        )
        assert resp.status_code == 200
        assert resp.json()["is_anomaly"] is True

    def test_list_anomalies(self, auth):
        resp = client.get("/api/ml/anomalies", headers=auth["headers"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_score_unauthorized(self):
        resp = client.post("/api/ml/score", json={"service": "svc", "metrics": [0.5]})
        assert resp.status_code in (401, 403)


class TestAnalyticsEndpoints:
    def test_incident_summary(self, auth):
        resp = client.get("/api/analytics/incidents/summary", headers=auth["headers"])
        assert resp.status_code == 200
        data = resp.json()
        assert "total_incidents" in data
        assert "by_severity" in data
        assert "mttr_minutes" in data

    def test_top_errors(self, auth):
        resp = client.get("/api/analytics/logs/top-errors", headers=auth["headers"])
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_alert_trend(self, auth):
        resp = client.get("/api/analytics/alerts/trend", headers=auth["headers"])
        assert resp.status_code == 200
        data = resp.json()
        assert "total_alerts" in data
        assert "resolved_alerts" in data

    def test_containers_endpoint(self, auth):
        resp = client.get("/api/integrations/containers", headers=auth["headers"])
        assert resp.status_code == 200
        data = resp.json()
        assert "docker" in data
        assert "kubernetes" in data
        assert isinstance(data["docker"], list)
        # k8s returns [] gracefully without kubeconfig
        assert isinstance(data["kubernetes"], list)
