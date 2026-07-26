"""Persist AI provider settings to DB so they survive restarts."""
import logging
import os
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from src.backend.shared_models import SystemSetting

logger = logging.getLogger(__name__)

_AI_KEYS = {
    "AI_PROVIDER": None,
    "ANTHROPIC_API_KEY": None,
    "GEMINI_API_KEY": None,
    "OPENROUTER_API_KEY": None,
    "NVAPI_KEY": None,
}


def load_ai_settings_from_db(db: Session) -> None:
    for key in _AI_KEYS:
        if os.getenv(key):
            continue
        row = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if row and row.value:
            os.environ[key] = row.value
            logger.info("Restored %s from DB setting", key)


def save_ai_settings(
    db: Session,
    provider: str | None = None,
    openrouter_key: str | None = None,
    nvapi_key: str | None = None,
) -> None:
    now = datetime.now(timezone.utc)
    pairs = {}
    if provider:
        pairs["AI_PROVIDER"] = provider
    if openrouter_key:
        pairs["OPENROUTER_API_KEY"] = openrouter_key
    if nvapi_key:
        pairs["NVAPI_KEY"] = nvapi_key
    for key, value in pairs.items():
        row = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if row:
            row.value = value
            row.updated_at = now
        else:
            db.add(SystemSetting(key=key, value=value, created_at=now, updated_at=now))
        os.environ[key] = value
        logger.info("Persisted %s to DB", key)
    if pairs:
        db.commit()
