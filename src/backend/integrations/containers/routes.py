"""Container monitoring endpoint — merged Docker + Kubernetes view."""
from fastapi import APIRouter, Depends

from src.backend.auth.dependencies import get_current_user_dependency

router = APIRouter(prefix="/api/integrations", tags=["containers"])


@router.get("/containers")
async def list_containers(
    current_user: dict = Depends(get_current_user_dependency),
):
    from src.backend.integrations.docker.client import list_containers as docker_list
    from src.backend.integrations.k8s.client import list_pods

    docker_result = docker_list()
    k8s_result = list_pods()

    containers = docker_result["containers"]
    pods = k8s_result["pods"]

    return {
        "docker": {
            "available": docker_result["available"],
            "reason": docker_result["reason"],
            "containers": containers,
        },
        "kubernetes": {
            "available": k8s_result["available"],
            "reason": k8s_result["reason"],
            "pods": pods,
        },
        "total": len(containers) + len(pods),
        "unhealthy": [
            c for c in containers + pods
            if c.get("health") not in ("healthy", "unknown") or c.get("status") not in ("running", "Running")
        ],
    }
