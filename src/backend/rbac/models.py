from enum import Enum
from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class Role(str, Enum):
    OWNER = "owner"
    RESPONDER = "responder"
    VIEWER = "viewer"


class UserContext(BaseModel):
    id: UUID
    team_id: UUID
    role: Role
    email: str
    is_active: bool = True
