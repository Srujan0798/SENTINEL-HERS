import uuid
import hashlib
import secrets
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from src.backend.auth.dependencies import get_current_user_dependency
from src.backend.db import get_db
from src.backend.apikeys.models import ApiKey

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/keys", tags=["api-keys"])

class ApiKeyOut(BaseModel):
    id: str
    name: str
    prefix: str
    permissions: str
    is_active: bool
    last_used_at: Optional[str] = None
    created_at: Optional[str] = None

class ApiKeyFullOut(ApiKeyOut):
    key: str  # full key, only shown once on creation

class CreateKeyRequest(BaseModel):
    name: str
    permissions: str = "read"

@router.get("", response_model=list[ApiKeyOut])
async def list_keys(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    keys = db.query(ApiKey).filter(
        ApiKey.team_id == current_user["team_id"],
        ApiKey.is_active == True,
    ).all()
    return [
        ApiKeyOut(
            id=str(k.id), name=k.name, prefix=k.prefix,
            permissions=k.permissions, is_active=k.is_active,
            last_used_at=k.last_used_at.isoformat() if k.last_used_at else None,
            created_at=k.created_at.isoformat() if k.created_at else None,
        ) for k in keys
    ]

@router.post("", response_model=ApiKeyFullOut, status_code=201)
async def create_key(
    body: CreateKeyRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    raw_key = f"sk-{secrets.token_hex(24)}"
    prefix = raw_key[:11]  # "sk-" + 8 hex chars
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key = ApiKey(
        id=str(uuid.uuid4()),
        team_id=current_user["team_id"],
        user_id=current_user["id"],
        name=body.name,
        prefix=prefix,
        key_hash=key_hash,
        permissions=body.permissions,
        is_active=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(key)
    db.commit()
    logger.info("Created API key %s for team %s", prefix, current_user["team_id"])
    return ApiKeyFullOut(
        id=str(key.id), name=key.name, prefix=key.prefix,
        permissions=key.permissions, is_active=key.is_active,
        key=raw_key,
    )

@router.delete("/{key_id}", status_code=204)
async def delete_key(
    key_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    key = db.query(ApiKey).filter(
        ApiKey.id == key_id,
        ApiKey.team_id == current_user["team_id"],
    ).first()
    if not key:
        raise HTTPException(status_code=404, detail="Key not found")
    key.is_active = False
    db.commit()
    logger.info("Revoked API key %s", key.prefix)
