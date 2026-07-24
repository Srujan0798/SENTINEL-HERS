"""Docker container status reader — graceful fallback if daemon unavailable."""
import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    import docker as _docker
    _DOCKER_AVAILABLE = True
except ImportError:
    _docker = None
    _DOCKER_AVAILABLE = False


def list_containers() -> dict[str, Any]:
    """Return running containers with availability info.

    On success: {"available": True, "containers": [...]}
    On failure: {"available": False, "reason": "<error>", "containers": []}
    Never crashes — FM-11 fail loud via logging, graceful surface to caller.
    """
    if not _DOCKER_AVAILABLE:
        return {
            "available": False,
            "reason": "docker Python package not installed",
            "containers": [],
        }
    try:
        client = _docker.from_env()
        containers = client.containers.list()
        result = []
        for c in containers:
            stats = {}
            try:
                raw = c.stats(stream=False)
                cpu_delta = raw["cpu_stats"]["cpu_usage"]["total_usage"] - raw["precpu_stats"]["cpu_usage"]["total_usage"]
                sys_delta = raw["cpu_stats"]["system_cpu_usage"] - raw["precpu_stats"].get("system_cpu_usage", 0)
                cpu_pct = (cpu_delta / sys_delta) * 100 if sys_delta > 0 else 0.0
                mem_usage = raw["memory_stats"].get("usage", 0)
                mem_mb = mem_usage / (1024 * 1024)
                stats = {"cpu_pct": round(cpu_pct, 2), "mem_mb": round(mem_mb, 1)}
            except Exception:
                stats = {"cpu_pct": 0.0, "mem_mb": 0.0}

            result.append({
                "name": c.name,
                "image": c.image.tags[0] if c.image.tags else c.image.id[:12],
                "status": c.status,
                "health": c.attrs.get("State", {}).get("Health", {}).get("Status", "unknown"),
                "cpu_pct": stats["cpu_pct"],
                "mem_mb": stats["mem_mb"],
                "started_at": c.attrs.get("State", {}).get("StartedAt", ""),
                "source": "docker",
            })
        return {"available": True, "reason": None, "containers": result}
    except Exception as exc:
        logger.warning("Docker daemon unavailable: %s", exc)
        return {
            "available": False,
            "reason": str(exc),
            "containers": [],
        }
