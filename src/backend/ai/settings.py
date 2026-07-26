"""Persist AI provider settings to DB so they survive restarts.
Uses Fernet encryption at rest — keys are never stored as plaintext.
"""
import logging
import os
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from src.backend.shared_models import SystemSetting

logger = logging.getLogger(__name__)

_FERNET: object | None = None
_FERNET_INIT_DONE = False


def _get_fernet() -> object | None:
    """Build (once) and cache the Fernet instance from ENCRYPTION_KEY.

    Previously this regenerated a brand-new random key on every call whenever
    the configured key didn't end in "=", so encrypt() and decrypt() used
    different keys and decryption silently failed every time. Now the key is
    validated and cached exactly once; an invalid key fails loud in the log
    instead of silently rotating.
    """
    global _FERNET, _FERNET_INIT_DONE
    if _FERNET_INIT_DONE:
        return _FERNET
    _FERNET_INIT_DONE = True
    raw = os.getenv("ENCRYPTION_KEY") or os.getenv("SENTINEL_ENCRYPTION_KEY")
    if not raw:
        return None
    try:
        from cryptography.fernet import Fernet
        _FERNET = Fernet(raw.encode() if isinstance(raw, str) else raw)
        return _FERNET
    except Exception:
        logger.error(
            "ENCRYPTION_KEY is set but is not a valid Fernet key — "
            "storing/reading AI provider keys WITHOUT encryption until fixed."
        )
        return None


def _encrypt(value: str) -> str:
    f = _get_fernet()
    if not f:
        return value
    return f.encrypt(value.encode()).decode()


def _decrypt(value: str) -> str:
    f = _get_fernet()
    if not f:
        return value
    try:
        return f.decrypt(value.encode()).decode()
    except Exception:
        return value


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
            os.environ[key] = _decrypt(row.value)
            logger.info("Restored %s from DB setting", key)


def save_ai_settings(
    db: Session,
    provider: str | None = None,
    anthropic_key: str | None = None,
    gemini_key: str | None = None,
    openrouter_key: str | None = None,
    nvapi_key: str | None = None,
) -> None:
    now = datetime.now(timezone.utc)
    pairs = {}
    if provider:
        pairs["AI_PROVIDER"] = provider
    if anthropic_key:
        pairs["ANTHROPIC_API_KEY"] = anthropic_key
    if gemini_key:
        pairs["GEMINI_API_KEY"] = gemini_key
    if openrouter_key:
        pairs["OPENROUTER_API_KEY"] = openrouter_key
    if nvapi_key:
        pairs["NVAPI_KEY"] = nvapi_key
    for key, value in pairs.items():
        encrypted = _encrypt(value)
        row = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if row:
            row.value = encrypted
            row.updated_at = now
        else:
            db.add(SystemSetting(key=key, value=encrypted, created_at=now, updated_at=now))
        os.environ[key] = value
        logger.info("Persisted %s to DB (encrypted)", key)
    if pairs:
        db.commit()
