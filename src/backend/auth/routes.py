from fastapi import APIRouter, Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.backend.rate_limit import limiter
from src.backend.db import get_db
from .models import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse
from .service import (
    get_current_user,
    get_user_response,
    login,
    refresh_token,
    register,
)

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
    return register(body, db)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login_user(request: Request, body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return login(body, db)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/minute")
async def refresh_access_token(request: Request, body: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return refresh_token(body, db)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: dict = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
) -> UserResponse:
    return get_user_response(current_user["id"], db)
