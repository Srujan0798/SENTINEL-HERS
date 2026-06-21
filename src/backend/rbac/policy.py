from .models import Role


POLICY: dict[str, set[Role]] = {
    "incidents:read": {Role.OWNER, Role.RESPONDER, Role.VIEWER},
    "incidents:create": {Role.OWNER, Role.RESPONDER},
    "incidents:update": {Role.OWNER, Role.RESPONDER},
    "incidents:delete": {Role.OWNER},
    "incidents:triage": {Role.OWNER, Role.RESPONDER},
    "incidents:assign": {Role.OWNER, Role.RESPONDER},
    "incidents:resolve": {Role.OWNER, Role.RESPONDER},
    "incidents:escalate": {Role.OWNER},
    "incidents:comment": {Role.OWNER, Role.RESPONDER},
    "tasks:read": {Role.OWNER, Role.RESPONDER, Role.VIEWER},
    "tasks:create": {Role.OWNER, Role.RESPONDER},
    "tasks:update": {Role.OWNER, Role.RESPONDER},
    "tasks:delete": {Role.OWNER},
    "channels:read": {Role.OWNER, Role.RESPONDER, Role.VIEWER},
    "channels:create": {Role.OWNER, Role.RESPONDER},
    "channels:write": {Role.OWNER, Role.RESPONDER},
    "sla:read": {Role.OWNER, Role.RESPONDER, Role.VIEWER},
    "sla:update": {Role.OWNER},
    "logs:read": {Role.OWNER, Role.RESPONDER, Role.VIEWER},
    "logs:write": {Role.OWNER, Role.RESPONDER},
    "health:read": {Role.OWNER, Role.RESPONDER, Role.VIEWER},
    "deployments:read": {Role.OWNER, Role.RESPONDER, Role.VIEWER},
    "deployments:create": {Role.OWNER},
    "commits:read": {Role.OWNER, Role.RESPONDER, Role.VIEWER},
    "analytics:read": {Role.OWNER, Role.RESPONDER, Role.VIEWER},
    "analytics:write": {Role.OWNER},
    "users:read": {Role.OWNER, Role.RESPONDER, Role.VIEWER},
    "users:manage": {Role.OWNER},
    "team:read": {Role.OWNER, Role.RESPONDER, Role.VIEWER},
    "team:manage": {Role.OWNER},
}


def check_permission(role: Role, action: str) -> bool:
    allowed_roles = POLICY.get(action)
    if allowed_roles is None:
        return False
    return role in allowed_roles
