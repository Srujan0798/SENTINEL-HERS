import logging
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.backend.auth.dependencies import get_current_user_dependency
from src.backend.db import get_db
from src.backend.notifications.models import NotificationPreference

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationPrefOut(BaseModel):
    channel: str
    enabled: bool
    config: Optional[str] = None


class NotificationPrefsOut(BaseModel):
    preferences: list[NotificationPrefOut]


class UpdatePrefsRequest(BaseModel):
    email: Optional[bool] = None
    slack: Optional[bool] = None
    pagerduty: Optional[bool] = None


_DEFAULT_CHANNELS = ["email", "slack", "pagerduty"]


def _get_or_create_pref(db: Session, user_id: str, channel: str) -> NotificationPreference:
    pref = db.query(NotificationPreference).filter(
        NotificationPreference.user_id == user_id,
        NotificationPreference.channel == channel,
    ).first()
    if not pref:
        pref = NotificationPreference(
            id=None,
            user_id=user_id,
            channel=channel,
            enabled=True,
            config={"email": None, "slack": "#incidents", "pagerduty": "SEV1/SEV2"}.get(channel),
        )
        db.add(pref)
        db.flush()
    return pref


@router.get("/preferences", response_model=NotificationPrefsOut)
async def get_preferences(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    user_id = current_user["id"]
    prefs = []
    for ch in _DEFAULT_CHANNELS:
        pref = _get_or_create_pref(db, user_id, ch)
        prefs.append(NotificationPrefOut(channel=pref.channel, enabled=pref.enabled, config=pref.config))
    db.commit()
    return NotificationPrefsOut(preferences=prefs)


@router.post("/preferences", response_model=NotificationPrefsOut)
async def update_preferences(
    body: UpdatePrefsRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency),
):
    user_id = current_user["id"]
    mapping = {"email": body.email, "slack": body.slack, "pagerduty": body.pagerduty}
    for channel, enabled in mapping.items():
        if enabled is not None:
            pref = _get_or_create_pref(db, user_id, channel)
            pref.enabled = enabled
    db.commit()
    prefs = []
    for ch in _DEFAULT_CHANNELS:
        pref = _get_or_create_pref(db, user_id, ch)
        prefs.append(NotificationPrefOut(channel=pref.channel, enabled=pref.enabled, config=pref.config))
    return NotificationPrefsOut(preferences=prefs)
