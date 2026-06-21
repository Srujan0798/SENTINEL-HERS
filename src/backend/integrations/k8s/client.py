"""Kubernetes pod status reader — returns [] if kubeconfig unavailable."""
import logging
from typing import Any

logger = logging.getLogger(__name__)


def list_pods() -> list[dict[str, Any]]:
    """Return running pods. Returns [] if kubeconfig not found (FM-11: fail gracefully)."""
    try:
        from kubernetes import client, config
        try:
            config.load_kube_config()
        except Exception:
            config.load_incluster_config()

        v1 = client.CoreV1Api()
        pods = v1.list_pod_for_all_namespaces(watch=False)
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
        return result
    except Exception as exc:
        logger.warning("Kubernetes unavailable (no kubeconfig?): %s", exc)
        return []
