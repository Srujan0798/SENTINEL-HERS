"""Kubernetes pod status reader — graceful fallback if kubeconfig unavailable."""
import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from kubernetes import client as _k8s_client, config as _k8s_config
    _K8S_AVAILABLE = True
except ImportError:
    _k8s_client = None
    _k8s_config = None
    _K8S_AVAILABLE = False


def list_pods() -> dict[str, Any]:
    """Return running pods with availability info.

    On success: {"available": True, "pods": [...]}
    On failure: {"available": False, "reason": "<error>", "pods": []}
    Never crashes — FM-11 fail loud via logging, graceful surface to caller.
    """
    if not _K8S_AVAILABLE:
        return {
            "available": False,
            "reason": "kubernetes Python package not installed",
            "pods": [],
        }
    try:
        try:
            _k8s_config.load_kube_config()
        except Exception:
            _k8s_config.load_incluster_config()

        v1 = _k8s_client.CoreV1Api()
        pods = v1.list_pod_for_all_namespaces(watch=False, _request_timeout=3)
        result = []
        for pod in pods.items:
            conditions = {c.type: c.status for c in (pod.status.conditions or [])}
            result.append({
                "name": pod.metadata.name,
                "image": pod.spec.containers[0].image if pod.spec.containers else "unknown",
                "status": pod.status.phase or "Unknown",
                "health": "healthy" if conditions.get("Ready") == "True" else "unhealthy",
                "cpu_pct": 0.0,
                "mem_mb": 0.0,
                "started_at": str(pod.status.start_time) if pod.status.start_time else "",
                "source": "kubernetes",
                "namespace": pod.metadata.namespace,
            })
        return {"available": True, "reason": None, "pods": result}
    except Exception as exc:
        logger.warning("Kubernetes unavailable (no kubeconfig?): %s", exc)
        return {
            "available": False,
            "reason": str(exc),
            "pods": [],
        }
