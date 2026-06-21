from typing import Callable
from fastapi import Depends, HTTPException, status

from .models import Role, UserContext
from .policy import check_permission


async def _get_current_user_placeholder() -> UserContext:
    raise NotImplementedError(
        "get_current_user not wired — auth module must override via app.dependency_overrides"
    )


def require_role(*allowed_roles: Role) -> Callable:
    async def _guard(
        current_user: UserContext = Depends(_get_current_user_placeholder),
    ) -> UserContext:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role.value}' lacks required permission",
            )
        return current_user

    return _guard


def require_permission(action: str) -> Callable:
    async def _guard(
        current_user: UserContext = Depends(_get_current_user_placeholder),
    ) -> UserContext:
        if not check_permission(current_user.role, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role.value}' lacks permission for '{action}'",
            )
        return current_user

    return _guard
