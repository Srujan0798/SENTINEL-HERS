from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from typing import Optional
from datetime import datetime


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str
    team_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


class RoleResponse(BaseModel):
    """Nested role so the FE can gate nav (useRole → role.name) without a second call."""

    id: str
    name: str
    permissions: list[str] = []
    description: Optional[str] = None


class UserResponse(BaseModel):
    id: UUID
    team_id: UUID
    email: str
    name: str
    avatar_url: Optional[str] = None
    role_id: Optional[str] = None
    role: Optional[RoleResponse] = None
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


TokenResponse.model_rebuild()
