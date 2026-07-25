"""Container monitoring endpoint — merged Docker + Kubernetes view."""
import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, Depends

from src.backend.auth.dependencies import get_current_user_dependency

router = APIRouter(prefix="/api/integrations", tags=["containers"])

_executor = ThreadPoolExecutor(max_workers=2)


def _empty_docker(reason: str) -> dict:
    return {"available": False, "reason": reason, "containers": []}


def _empty_k8s(reason: str) -> dict:
    return {"available": False, "reason": reason, "pods": []}


@router.get("/containers")
async def list_containers(
    current_user: dict = Depends(get_current_user_dependency),
):
    """Merged Docker + K8s view with hard wall-clock timeout (PaaS safe)."""
    from src.backend.integrations.docker.client import list_containers as docker_list
    from src.backend.integrations.k8s.client import list_pods

    loop = asyncio.get_event_loop()

    async def _run(fn, empty):
        try:
            return await asyncio.wait_for(
                loop.run_in_executor(_executor, fn),
                timeout=3.5,
            )
        except Exception as exc:
            return empty(str(exc) or "probe timed out")

    docker_result, k8s_result = await asyncio.gather(
        _run(docker_list, _empty_docker),
        _run(list_pods, _empty_k8s),
    )

    containers = docker_result.get("containers") or []
    pods = k8s_result.get("pods") or []

    return {
        "docker": {
            "available": docker_result.get("available", False),
            "reason": docker_result.get("reason"),
            "containers": containers,
        },
        "kubernetes": {
            "available": k8s_result.get("available", False),
            "reason": k8s_result.get("reason"),
            "pods": pods,
        },
        "total": len(containers) + len(pods),
        "unhealthy": [
            c
            for c in containers + pods
            if c.get("health") not in ("healthy", "unknown")
            or c.get("status") not in ("running", "Running")
        ],
    }
