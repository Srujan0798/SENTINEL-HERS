from typing import Callable
from fastapi import Depends, HTTPException, status

from src.backend.auth.dependencies import get_current_user_dependency
from .models import Role, UserContext
from .policy import check_permission


_MAP = {
    "admin": Role.ADMIN,
    "owner": Role.OWNER,
    "responder": Role.RESPONDER,
    "viewer": Role.VIEWER,
}


def _to_user_context(d: dict) -> UserContext:
    raw_role = d.get("role", "")
    role = _MAP.get(raw_role)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Unknown role '{raw_role}'",
        )
    return UserContext(
        id=d["id"],
        team_id=d["team_id"],
        role=role,
        email=d.get("email", ""),
        is_active=d.get("is_active", True),
    )


def require_role(*allowed_roles: Role) -> Callable:
    async def _guard(
        current_user: dict = Depends(get_current_user_dependency),
    ) -> UserContext:
        ctx = _to_user_context(current_user)
        if ctx.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{ctx.role.value}' lacks required permission",
            )
        return ctx

    return _guard


def require_permission(action: str) -> Callable:
    async def _guard(
        current_user: dict = Depends(get_current_user_dependency),
    ) -> UserContext:
        ctx = _to_user_context(current_user)
        if not check_permission(ctx.role, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{ctx.role.value}' lacks permission for '{action}'",
            )
        return ctx

    return _guard
