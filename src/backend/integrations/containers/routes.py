"""Container monitoring endpoint — merged Docker + Kubernetes view."""
from fastapi import APIRouter, Depends

from src.backend.auth.dependencies import get_current_user_dependency

router = APIRouter(prefix="/api/integrations", tags=["containers"])


@router.get("/containers")
async def list_containers(
    current_user: dict = Depends(get_current_user_dependency),
):
    from src.backend.integrations.docker.client import list_containers as docker_containers
    from src.backend.integrations.k8s.client import list_pods

    containers = docker_containers()
    pods = list_pods()

    return {
        "docker": containers,
        "kubernetes": pods,
        "total": len(containers) + len(pods),
        "unhealthy": [
            c for c in containers + pods
            if c.get("health") not in ("healthy", "unknown") or c.get("status") not in ("running", "Running")
        ],
    }
