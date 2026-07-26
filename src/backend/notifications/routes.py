import logging
import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.backend.auth.dependencies import get_current_user_dependency
from src.backend.db import get_db
from src.backend.notifications.models import NotificationPreference
from src.backend.shared_models import SystemSetting
from src.backend.rbac.dependencies import require_role
from src.backend.rbac.models import Role, UserContext

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


class ChannelConfigOut(BaseModel):
    channel: str
    configured: bool
    hint: str


class EmailConfigRequest(BaseModel):
    host: str = ""
    port: int = 587
    user: str = ""
    password: str = ""
    sender: str = ""


class SlackConfigRequest(BaseModel):
    webhook_url: str = ""


class PagerDutyConfigRequest(BaseModel):
    routing_key: str = ""


_CHANNEL_HELP = {
    "email": "SMTP server credentials",
    "slack": "Slack Incoming Webhook URL (https://hooks.slack.com/services/...)",
    "pagerduty": "PagerDuty Events API v2 Routing Key",
}

_CHANNEL_SETTING_KEYS = {
    "email": ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "SMTP_FROM"],
    "slack": ["SLACK_WEBHOOK_URL"],
    "pagerduty": ["PAGERDUTY_ROUTING_KEY"],
}


def _save_channel_config(db: Session, channel: str, config: dict[str, str]) -> None:
    from datetime import datetime, timezone
    import os
    now = datetime.now(timezone.utc)
    for key, value in config.items():
        if not value:
            continue
        setting_key = f"NOTIFY_{key}"
        row = db.query(SystemSetting).filter(SystemSetting.key == setting_key).first()
        if row:
            row.value = value
            row.updated_at = now
        else:
            db.add(SystemSetting(key=setting_key, value=value, created_at=now, updated_at=now))
        os.environ[key] = value
    db.commit()


@router.get("/channels", response_model=list[ChannelConfigOut])
async def get_channel_configs(
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_role(Role.ADMIN)),
):
    import os
    results = []
    for channel, keys in _CHANNEL_SETTING_KEYS.items():
        configured = all(os.getenv(k) for k in keys)
        if not configured:
            for k in keys:
                row = db.query(SystemSetting).filter(SystemSetting.key == f"NOTIFY_{k}").first()
                if row and row.value:
                    configured = True
                    os.environ[k] = row.value
                    break
        results.append(ChannelConfigOut(channel=channel, configured=configured, hint=_CHANNEL_HELP.get(channel, "")))
    return results


@router.post("/channels/email")
async def configure_email(
    body: EmailConfigRequest,
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_role(Role.ADMIN)),
):
    import os
    config = {"SMTP_HOST": body.host, "SMTP_PORT": str(body.port), "SMTP_USER": body.user, "SMTP_PASSWORD": body.password, "SMTP_FROM": body.sender}
    _save_channel_config(db, "email", {k: v for k, v in config.items() if v})
    for k, v in config.items():
        if v:
            os.environ[k] = v
    return {"status": "ok", "channel": "email"}


@router.post("/channels/slack")
async def configure_slack(
    body: SlackConfigRequest,
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_role(Role.ADMIN)),
):
    import os
    if body.webhook_url:
        _save_channel_config(db, "slack", {"SLACK_WEBHOOK_URL": body.webhook_url})
        os.environ["SLACK_WEBHOOK_URL"] = body.webhook_url
    return {"status": "ok", "channel": "slack"}


@router.post("/channels/pagerduty")
async def configure_pagerduty(
    body: PagerDutyConfigRequest,
    db: Session = Depends(get_db),
    _: UserContext = Depends(require_role(Role.ADMIN)),
):
    import os
    if body.routing_key:
        _save_channel_config(db, "pagerduty", {"PAGERDUTY_ROUTING_KEY": body.routing_key})
        os.environ["PAGERDUTY_ROUTING_KEY"] = body.routing_key
    return {"status": "ok", "channel": "pagerduty"}
