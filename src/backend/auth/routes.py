import uuid
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.backend.rate_limit import limiter
from src.backend.db import get_db
from src.backend.shared_models import UserModel, TeamModel, RoleModel
from src.backend.rbac.dependencies import require_role
from src.backend.rbac.models import Role, UserContext
from .models import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse
from .service import (
    get_current_user,
    get_user_response,
    login,
    refresh_token,
    register,
    hash_password,
)
from src.backend.shared.services import get_auth_service, get_user_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


async def get_current_user_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> dict:
    return get_current_user(credentials.credentials, db)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("60/minute")
async def register_user(request: Request, body: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    auth_service = get_auth_service(db)
    return auth_service.register_user(body)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login_user(request: Request, body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    auth_service = get_auth_service(db)
    return auth_service.login_user(body)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/minute")
async def refresh_access_token(request: Request, body: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    auth_service = get_auth_service(db)
    return auth_service.refresh_token(body)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: dict = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
) -> UserResponse:
    return get_user_response(current_user["id"], db)


class InviteRequest(BaseModel):
    email: str
    name: str = ""
    role_name: str = "responder"


class InviteResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    team_id: str
    status: str = "invited"


@router.post("/invite", response_model=InviteResponse, status_code=201)
async def invite_member(
    body: InviteRequest,
    db: Session = Depends(get_db),
    ctx: UserContext = Depends(require_role(Role.ADMIN, Role.OWNER)),
):
    existing = db.query(UserModel).filter(UserModel.email == body.email).first()
    if existing:
        if str(existing.team_id) == str(ctx.team_id):
            raise HTTPException(status_code=400, detail="User is already a member of this team")
        raise HTTPException(status_code=400, detail="User already registered under another team")

    role = db.query(RoleModel).filter(RoleModel.name == body.role_name).first()
    if not role:
        raise HTTPException(status_code=400, detail=f"Unknown role: {body.role_name}")

    temp_pw = uuid.uuid4().hex[:16]
    user = UserModel(
        id=str(uuid.uuid4()),
        team_id=str(ctx.team_id),
        email=body.email,
        password_hash=hash_password(temp_pw),
        name=body.name or body.email.split("@")[0],
        role_id=str(role.id),
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    logger.info("Invited %s (%s) to team %s", body.email, body.role_name, ctx.team_id)
    return InviteResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        role=body.role_name,
        team_id=str(ctx.team_id),
        status="invited",
    )
