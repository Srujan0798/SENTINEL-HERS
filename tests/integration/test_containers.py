"""Integration tests for container monitoring — mocked docker/k8s clients."""
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_containers.db")
os.environ.setdefault("JWT_SECRET", "test-secret-key-long-enough-32ch!!")
os.environ.setdefault("JWT_REFRESH_SECRET", "test-refresh-long-enough-32ch!!")
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("AI_PROVIDER", "mock")

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

engine = create_engine("sqlite:///./test_containers.db", connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def setup_db():
    app.dependency_overrides[get_db] = override_db
    Base.metadata.create_all(bind=engine)
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    Path("test_containers.db").unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Docker client tests
# ---------------------------------------------------------------------------

class TestDockerClientAvailable:
    """Docker daemon reachable — returns containers with available:true."""

    def test_returns_available_true(self):
        from src.backend.integrations.docker.client import list_containers

        mock_container = MagicMock()
        mock_container.name = "web-app"
        mock_container.image.tags = ["nginx:1.25"]
        mock_container.status = "running"
        mock_container.attrs = {"State": {"Health": {"Status": "healthy"}, "StartedAt": "2025-01-01T00:00:00Z"}}
        mock_container.stats.return_value = {
            "cpu_stats": {"cpu_usage": {"total_usage": 1000}, "system_cpu_usage": 10000},
            "precpu_stats": {"cpu_usage": {"total_usage": 500}, "system_cpu_usage": 9000},
            "memory_stats": {"usage": 52428800},
        }

        mock_docker_mod = MagicMock()
        mock_docker_mod.from_env.return_value.containers.list.return_value = [mock_container]

        with patch("src.backend.integrations.docker.client._docker", mock_docker_mod), \
             patch("src.backend.integrations.docker.client._DOCKER_AVAILABLE", True):
            result = list_containers()

        assert result["available"] is True
        assert result["reason"] is None
        assert len(result["containers"]) == 1
        assert result["containers"][0]["name"] == "web-app"
        assert result["containers"][0]["source"] == "docker"

    def test_no_env_secrets_in_output(self):
        from src.backend.integrations.docker.client import list_containers

        mock_container = MagicMock()
        mock_container.name = "db"
        mock_container.image.tags = ["postgres:16"]
        mock_container.status = "running"
        mock_container.attrs = {"State": {"Health": {}, "StartedAt": ""}}
        mock_container.stats.return_value = {
            "cpu_stats": {"cpu_usage": {"total_usage": 0}, "system_cpu_usage": 100},
            "precpu_stats": {"cpu_usage": {"total_usage": 0}, "system_cpu_usage": 100},
            "memory_stats": {"usage": 0},
        }

        mock_docker_mod = MagicMock()
        mock_docker_mod.from_env.return_value.containers.list.return_value = [mock_container]

        with patch("src.backend.integrations.docker.client._docker", mock_docker_mod), \
             patch("src.backend.integrations.docker.client._DOCKER_AVAILABLE", True):
            result = list_containers()

        container = result["containers"][0]
        allowed_keys = {"name", "image", "status", "health", "cpu_pct", "mem_mb", "started_at", "source"}
        assert set(container.keys()) == allowed_keys


class TestDockerClientUnavailable:
    """Docker daemon unreachable — returns available:false + reason."""

    def test_returns_available_false_with_reason(self):
        from src.backend.integrations.docker.client import list_containers

        mock_docker_mod = MagicMock()
        mock_docker_mod.from_env.side_effect = ConnectionRefusedError("Cannot connect to Docker daemon")

        with patch("src.backend.integrations.docker.client._docker", mock_docker_mod), \
             patch("src.backend.integrations.docker.client._DOCKER_AVAILABLE", True):
            result = list_containers()

        assert result["available"] is False
        assert "Cannot connect to Docker daemon" in result["reason"]
        assert result["containers"] == []

    def test_import_error_returns_unavailable(self):
        from src.backend.integrations.docker.client import list_containers

        with patch("src.backend.integrations.docker.client._docker", None), \
             patch("src.backend.integrations.docker.client._DOCKER_AVAILABLE", False):
            result = list_containers()

        assert result["available"] is False
        assert result["containers"] == []


# ---------------------------------------------------------------------------
# Kubernetes client tests
# ---------------------------------------------------------------------------

class TestK8sClientAvailable:
    """K8s cluster reachable — returns pods with available:true."""

    def test_returns_available_true(self):
        from src.backend.integrations.k8s.client import list_pods

        mock_pod = MagicMock()
        mock_pod.metadata.name = "pod-abc-123"
        mock_pod.metadata.namespace = "default"
        mock_pod.spec.containers = [MagicMock(image="nginx:latest")]
        mock_pod.status.phase = "Running"
        mock_pod.status.conditions = [MagicMock(type="Ready", status="True")]
        mock_pod.status.start_time = "2025-01-01T00:00:00Z"

        mock_v1 = MagicMock()
        mock_v1.list_pod_for_all_namespaces.return_value.items = [mock_pod]

        mock_k8s_config = MagicMock()
        mock_k8s_client_mod = MagicMock()
        mock_k8s_client_mod.CoreV1Api.return_value = mock_v1

        with patch("src.backend.integrations.k8s.client._k8s_config", mock_k8s_config), \
             patch("src.backend.integrations.k8s.client._k8s_client", mock_k8s_client_mod):
            result = list_pods()

        assert result["available"] is True
        assert result["reason"] is None
        assert len(result["pods"]) == 1
        assert result["pods"][0]["name"] == "pod-abc-123"
        assert result["pods"][0]["source"] == "kubernetes"
        assert result["pods"][0]["namespace"] == "default"
        assert result["pods"][0]["health"] == "healthy"

    def test_unhealthy_pod(self):
        from src.backend.integrations.k8s.client import list_pods

        mock_pod = MagicMock()
        mock_pod.metadata.name = "failing-pod"
        mock_pod.metadata.namespace = "kube-system"
        mock_pod.spec.containers = [MagicMock(image="redis:7")]
        mock_pod.status.phase = "Running"
        mock_pod.status.conditions = [MagicMock(type="Ready", status="False")]
        mock_pod.status.start_time = None

        mock_v1 = MagicMock()
        mock_v1.list_pod_for_all_namespaces.return_value.items = [mock_pod]

        mock_k8s_config = MagicMock()
        mock_k8s_client_mod = MagicMock()
        mock_k8s_client_mod.CoreV1Api.return_value = mock_v1

        with patch("src.backend.integrations.k8s.client._k8s_config", mock_k8s_config), \
             patch("src.backend.integrations.k8s.client._k8s_client", mock_k8s_client_mod):
            result = list_pods()

        assert result["available"] is True
        assert result["pods"][0]["health"] == "unhealthy"


class TestK8sClientUnavailable:
    """No kubeconfig / unreachable cluster — returns available:false + reason."""

    def test_returns_available_false_with_reason(self):
        from src.backend.integrations.k8s.client import list_pods

        mock_k8s_config = MagicMock()
        mock_k8s_config.load_kube_config.side_effect = FileNotFoundError("kubeconfig not found")
        mock_k8s_config.load_incluster_config.side_effect = FileNotFoundError("not in cluster")
        mock_k8s_client_mod = MagicMock()

        with patch("src.backend.integrations.k8s.client._k8s_config", mock_k8s_config), \
             patch("src.backend.integrations.k8s.client._k8s_client", mock_k8s_client_mod):
            result = list_pods()

        assert result["available"] is False
        assert result["reason"] is not None
        assert result["pods"] == []

    def test_cluster_timeout_returns_unavailable(self):
        from src.backend.integrations.k8s.client import list_pods

        mock_v1 = MagicMock()
        mock_v1.list_pod_for_all_namespaces.side_effect = TimeoutError("cluster unreachable")

        mock_k8s_config = MagicMock()
        mock_k8s_client_mod = MagicMock()
        mock_k8s_client_mod.CoreV1Api.return_value = mock_v1

        with patch("src.backend.integrations.k8s.client._k8s_config", mock_k8s_config), \
             patch("src.backend.integrations.k8s.client._k8s_client", mock_k8s_client_mod):
            result = list_pods()

        assert result["available"] is False
        assert "cluster unreachable" in result["reason"]

    def test_package_not_installed(self):
        from src.backend.integrations.k8s.client import list_pods

        with patch("src.backend.integrations.k8s.client._K8S_AVAILABLE", False):
            result = list_pods()

        assert result["available"] is False
        assert result["pods"] == []


# ---------------------------------------------------------------------------
# API route tests (FastAPI endpoint)
# ---------------------------------------------------------------------------

class TestContainersEndpointBothUnavailable:
    """Both Docker and K8s unavailable — endpoint returns available:false for both."""

    @patch("src.backend.integrations.k8s.client.list_pods")
    @patch("src.backend.integrations.docker.client.list_containers")
    def test_endpoint_returns_unavailable_fallback(self, mock_docker, mock_k8s):
        mock_docker.return_value = {
            "available": False,
            "reason": "Cannot connect to Docker daemon",
            "containers": [],
        }
        mock_k8s.return_value = {
            "available": False,
            "reason": "kubeconfig not found",
            "pods": [],
        }

        from src.backend.auth.dependencies import get_current_user_dependency
        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_user_dependency] = lambda: {
            "team_id": "test-team",
            "sub": "test@example.com",
        }
        try:
            resp = client.get("/api/integrations/containers")
            assert resp.status_code == 200
            body = resp.json()
            assert body["docker"]["available"] is False
            assert "Docker daemon" in body["docker"]["reason"]
            assert body["kubernetes"]["available"] is False
            assert "kubeconfig" in body["kubernetes"]["reason"]
            assert body["total"] == 0
            assert body["unhealthy"] == []
        finally:
            app.dependency_overrides.pop(get_current_user_dependency, None)
            app.dependency_overrides[get_db] = override_db


class TestContainersEndpointDockerAvailable:
    """Docker available, K8s unavailable — mixed state."""

    @patch("src.backend.integrations.k8s.client.list_pods")
    @patch("src.backend.integrations.docker.client.list_containers")
    def test_mixed_availability(self, mock_docker, mock_k8s):
        mock_docker.return_value = {
            "available": True,
            "reason": None,
            "containers": [
                {"name": "nginx", "image": "nginx:1.25", "status": "running", "health": "healthy",
                 "cpu_pct": 1.5, "mem_mb": 12.3, "started_at": "2025-01-01T00:00:00Z", "source": "docker"},
            ],
        }
        mock_k8s.return_value = {
            "available": False,
            "reason": "No kubeconfig",
            "pods": [],
        }

        from src.backend.auth.dependencies import get_current_user_dependency
        app.dependency_overrides[get_current_user_dependency] = lambda: {
            "team_id": "test-team",
            "sub": "test@example.com",
        }
        try:
            resp = client.get("/api/integrations/containers")
            assert resp.status_code == 200
            body = resp.json()
            assert body["docker"]["available"] is True
            assert body["kubernetes"]["available"] is False
            assert body["total"] == 1
            assert body["docker"]["containers"][0]["name"] == "nginx"
        finally:
            app.dependency_overrides.pop(get_current_user_dependency, None)


class TestContainersEndpointBothAvailable:
    """Both Docker and K8s available — returns all containers."""

    @patch("src.backend.integrations.k8s.client.list_pods")
    @patch("src.backend.integrations.docker.client.list_containers")
    def test_both_available(self, mock_docker, mock_k8s):
        mock_docker.return_value = {
            "available": True,
            "reason": None,
            "containers": [
                {"name": "app", "image": "app:v1", "status": "running", "health": "healthy",
                 "cpu_pct": 5.0, "mem_mb": 64.0, "started_at": "", "source": "docker"},
            ],
        }
        mock_k8s.return_value = {
            "available": True,
            "reason": None,
            "pods": [
                {"name": "worker-pod", "image": "worker:v2", "status": "Running", "health": "healthy",
                 "cpu_pct": 0.0, "mem_mb": 0.0, "started_at": "", "source": "kubernetes", "namespace": "default"},
            ],
        }

        from src.backend.auth.dependencies import get_current_user_dependency
        app.dependency_overrides[get_current_user_dependency] = lambda: {
            "team_id": "test-team",
            "sub": "test@example.com",
        }
        try:
            resp = client.get("/api/integrations/containers")
            assert resp.status_code == 200
            body = resp.json()
            assert body["docker"]["available"] is True
            assert body["kubernetes"]["available"] is True
            assert body["total"] == 2
        finally:
            app.dependency_overrides.pop(get_current_user_dependency, None)
