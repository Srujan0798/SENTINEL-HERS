from .models import Role


_ADMIN_ROLES = {Role.OWNER, Role.ADMIN}

POLICY: dict[str, set[Role]] = {
    "incidents:read": {Role.OWNER, Role.ADMIN, Role.RESPONDER, Role.VIEWER},
    "incidents:create": {Role.OWNER, Role.ADMIN, Role.RESPONDER},
    "incidents:update": {Role.OWNER, Role.ADMIN, Role.RESPONDER},
    "incidents:delete": {Role.OWNER, Role.ADMIN},
    "incidents:triage": {Role.OWNER, Role.ADMIN, Role.RESPONDER},
    "incidents:assign": {Role.OWNER, Role.ADMIN, Role.RESPONDER},
    "incidents:resolve": {Role.OWNER, Role.ADMIN, Role.RESPONDER},
    "incidents:escalate": {Role.OWNER, Role.ADMIN},
    "incidents:comment": {Role.OWNER, Role.ADMIN, Role.RESPONDER},
    "tasks:read": {Role.OWNER, Role.ADMIN, Role.RESPONDER, Role.VIEWER},
    "tasks:create": {Role.OWNER, Role.ADMIN, Role.RESPONDER},
    "tasks:update": {Role.OWNER, Role.ADMIN, Role.RESPONDER},
    "tasks:delete": {Role.OWNER, Role.ADMIN},
    "channels:read": {Role.OWNER, Role.ADMIN, Role.RESPONDER, Role.VIEWER},
    "channels:create": {Role.OWNER, Role.ADMIN, Role.RESPONDER},
    "channels:write": {Role.OWNER, Role.ADMIN, Role.RESPONDER},
    "sla:read": {Role.OWNER, Role.ADMIN, Role.RESPONDER, Role.VIEWER},
    "sla:update": {Role.OWNER, Role.ADMIN},
    "logs:read": {Role.OWNER, Role.ADMIN, Role.RESPONDER, Role.VIEWER},
    "logs:write": {Role.OWNER, Role.ADMIN, Role.RESPONDER},
    "health:read": {Role.OWNER, Role.ADMIN, Role.RESPONDER, Role.VIEWER},
    "deployments:read": {Role.OWNER, Role.ADMIN, Role.RESPONDER, Role.VIEWER},
    "deployments:create": {Role.OWNER, Role.ADMIN},
    "commits:read": {Role.OWNER, Role.ADMIN, Role.RESPONDER, Role.VIEWER},
    "analytics:read": {Role.OWNER, Role.ADMIN, Role.RESPONDER, Role.VIEWER},
    "analytics:write": {Role.OWNER, Role.ADMIN},
    "users:read": {Role.OWNER, Role.ADMIN, Role.RESPONDER, Role.VIEWER},
    "users:manage": {Role.OWNER, Role.ADMIN},
    "team:read": {Role.OWNER, Role.ADMIN, Role.RESPONDER, Role.VIEWER},
    "team:manage": {Role.OWNER, Role.ADMIN},
}


def check_permission(role: Role, action: str) -> bool:
    allowed_roles = POLICY.get(action)
    if allowed_roles is None:
        return False
    return role in allowed_roles
