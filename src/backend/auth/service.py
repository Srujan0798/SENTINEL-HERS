import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .models import (
    LoginRequest,
    RegisterRequest,
    RefreshRequest,
    RoleResponse,
    TokenResponse,
    UserResponse,
)
from src.backend.shared_models import RoleModel, TeamModel, UserModel, RevokedToken

_jwt = os.getenv("JWT_SECRET")
_jwt_refresh = os.getenv("JWT_REFRESH_SECRET")
_is_prod = os.getenv("ENV", "development").lower() in ("production", "prod")
if not _jwt or not _jwt_refresh:
    if _is_prod:
        raise RuntimeError(
            "JWT_SECRET and JWT_REFRESH_SECRET must be set in production."
        )
    _jwt = "dev-jwt-secret-do-not-use-in-prod"
    _jwt_refresh = "dev-jwt-refresh-secret-do-not-use-in-prod"
JWT_SECRET: str = _jwt
JWT_REFRESH_SECRET: str = _jwt_refresh
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def create_access_token(user_id: str, team_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        # ids may arrive as UUID objects from the ORM — cast to str so the
        # JWT payload is JSON-serializable.
        "sub": str(user_id),
        "team_id": str(team_id),
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def create_refresh_token(user_id: str, team_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "team_id": str(team_id),
        "role": role,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, JWT_REFRESH_SECRET, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def decode_refresh_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_REFRESH_SECRET, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


def get_user_by_email(db: Session, email: str) -> Optional[UserModel]:
    return db.query(UserModel).filter(UserModel.email == email).first()


def create_team(db: Session, name: str) -> TeamModel:
    # Team names are not unique (two orgs may share a name), so derive a unique
    # slug by appending a short suffix to the human-readable base.
    base_slug = name.lower().replace(" ", "-")
    slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
    team = TeamModel(
        id=str(uuid.uuid4()),
        name=name,
        slug=slug,
        created_at=datetime.now(timezone.utc),
    )
    db.add(team)
    db.flush()
    return team


def create_user(
    db: Session, email: str, password_hash: str, name: str, team_id: str
) -> UserModel:
    from src.backend.shared_models import RoleModel
    admin_role = db.query(RoleModel).filter(RoleModel.name == "admin").first()
    user = UserModel(
        id=str(uuid.uuid4()),
        team_id=team_id,
        email=email,
        password_hash=password_hash,
        name=name,
        role_id=str(admin_role.id) if admin_role else None,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    db.flush()
    return user


def get_user(db: Session, user_id: str) -> Optional[UserModel]:
    return db.query(UserModel).filter(UserModel.id == user_id).first()


def _resolve_role(db: Session, role_id) -> Optional[RoleModel]:
    if not role_id:
        return None
    return db.query(RoleModel).filter(RoleModel.id == str(role_id)).first()


def _role_name(db: Session, user: UserModel, default: str = "admin") -> str:
    """JWT + RBAC need a role *name* (admin/…), never a role_id UUID."""
    role = _resolve_role(db, getattr(user, "role_id", None))
    if role and role.name:
        return str(role.name)
    return default


def _user_response(user: UserModel, db: Optional[Session] = None) -> UserResponse:
    role_resp: Optional[RoleResponse] = None
    role_id = str(user.role_id) if user.role_id else None
    if db is not None and role_id:
        role = _resolve_role(db, role_id)
        if role:
            perms = role.permissions if isinstance(role.permissions, list) else []
            role_resp = RoleResponse(
                id=str(role.id),
                name=str(role.name),
                permissions=[str(p) for p in perms],
                description=role.description,
            )
    return UserResponse(
        id=user.id,
        team_id=user.team_id,
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        role_id=role_id,
        role=role_resp,
        is_active=user.is_active,
        last_login_at=getattr(user, "last_login_at", None),
        created_at=user.created_at,
        updated_at=getattr(user, "updated_at", user.created_at),
    )


def register(request: RegisterRequest, db: Session) -> TokenResponse:
    if get_user_by_email(db, request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    team = create_team(db, request.team_name)
    password_hash = hash_password(request.password)
    user = create_user(db, request.email, password_hash, request.name, team.id)
    db.commit()
    # re-load after commit so role_id is stable
    role_name = _role_name(db, user, default="admin")

    return TokenResponse(
        access_token=create_access_token(user.id, team.id, role_name),
        refresh_token=create_refresh_token(user.id, team.id, role_name),
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=_user_response(user, db),
    )


def login(request: LoginRequest, db: Session) -> TokenResponse:
    user = get_user_by_email(db, request.email)
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated",
        )

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    role_name = _role_name(db, user, default="admin")

    return TokenResponse(
        access_token=create_access_token(user.id, user.team_id, role_name),
        refresh_token=create_refresh_token(user.id, user.team_id, role_name),
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=_user_response(user, db),
    )


def refresh_token(request: RefreshRequest, db: Session) -> TokenResponse:
    payload = decode_refresh_token(request.refresh_token)
    old_jti = payload.get("jti")
    if old_jti:
        revoked = db.query(RevokedToken).filter(RevokedToken.jti == old_jti).first()
        if revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )
    user = get_user(db, payload.get("sub"))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated",
        )

    if old_jti:
        now_dt = datetime.now(timezone.utc)
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc) if payload.get("exp") else now_dt
        db.add(RevokedToken(jti=old_jti, user_id=str(user.id), revoked_at=now_dt, expires_at=exp))
        db.commit()

    role_name = _role_name(db, user, default="admin")
    return TokenResponse(
        access_token=create_access_token(user.id, user.team_id, role_name),
        refresh_token=create_refresh_token(user.id, user.team_id, role_name),
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=_user_response(user, db),
    )


def get_current_user(token: str, db: Session) -> dict:
    payload = decode_access_token(token)
    user = get_user(db, payload.get("sub"))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated",
        )
    # Prefer JWT role claim (already a name); fall back to DB role name.
    jwt_role = payload.get("role")
    role_name = (
        jwt_role
        if isinstance(jwt_role, str) and jwt_role and "-" not in jwt_role
        else _role_name(db, user, default="admin")
    )
    return {
        # cast UUID → str so downstream inserts/queries bind cleanly on SQLite
        "id": str(user.id),
        "team_id": str(user.team_id) if user.team_id else None,
        "role": role_name,
        "role_id": str(user.role_id) if user.role_id else None,
        "email": user.email,
        "name": user.name,
        "is_active": user.is_active,
    }


def get_user_response(user_id: str, db: Session) -> UserResponse:
    """Return a full UserResponse for the given user id (used by GET /auth/me)."""
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return _user_response(user, db)