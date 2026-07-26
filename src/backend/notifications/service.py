"""Notification dispatch service — sends via email/Slack/PagerDuty using channel configs from DB.
Each channel's credentials are stored in system_settings (encrypted), same pattern as AI settings.
If credentials are missing, dispatch logs the intent but doesn't fail — graceful degradation (FM-11).
"""
import logging
import os
from typing import Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Channel configs — stored in system_settings table
# --------------------------------------------------------------------------- #

CHANNEL_CONFIG_KEYS = {
    "email": {
        "host": "SMTP_HOST",
        "port": "SMTP_PORT",
        "user": "SMTP_USER",
        "password": "SMTP_PASSWORD",
        "from": "SMTP_FROM",
    },
    "slack": {
        "webhook_url": "SLACK_WEBHOOK_URL",
    },
    "pagerduty": {
        "routing_key": "PAGERDUTY_ROUTING_KEY",
        "api_key": "PAGERDUTY_API_KEY",
    },
}


def _get_config(db: Session, channel: str) -> dict[str, str]:
    from src.backend.shared_models import SystemSetting

    keys = CHANNEL_CONFIG_KEYS.get(channel, {})
    config = {}
    for setting_key, env_var in keys.items():
        val = os.getenv(env_var)
        if not val:
            row = db.query(SystemSetting).filter(SystemSetting.key == f"NOTIFY_{env_var}").first()
            if row and row.value:
                val = row.value
        if val:
            config[setting_key] = val
    return config


def dispatch_notification(
    db: Session,
    channel: str,
    recipient: str,
    subject: str,
    message: str,
    incident_id: Optional[str] = None,
) -> bool:
    if channel == "email":
        return _send_email(db, recipient, subject, message)
    elif channel == "slack":
        return _send_slack(db, recipient or "#incidents", subject, message)
    elif channel == "pagerduty":
        return _send_pagerduty(db, subject, message, incident_id)
    else:
        logger.warning("Unknown notification channel: %s", channel)
        return False


def _send_email(db: Session, to: str, subject: str, body: str) -> bool:
    config = _get_config(db, "email")
    if not config.get("host") or not config.get("from"):
        logger.info("[email] Not configured — would send to=%s subject=%s body=%s", to, subject, body[:80])
        return False
    try:
        import smtplib
        from email.mime.text import MIMEText

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = config["from"]
        msg["To"] = to
        port = int(config.get("port", 587))
        with smtplib.SMTP(config["host"], port) as server:
            server.starttls()
            if config.get("user") and config.get("password"):
                server.login(config["user"], config["password"])
            server.sendmail(config["from"], [to], msg.as_string())
        logger.info("[email] Sent to %s: %s", to, subject)
        return True
    except Exception as e:
        logger.warning("[email] Failed to send to %s: %s", to, e)
        return False


def _send_slack(db: Session, channel: str, subject: str, body: str) -> bool:
    config = _get_config(db, "slack")
    webhook_url = config.get("webhook_url")
    if not webhook_url:
        logger.info("[slack] Not configured — would post to=%s text=%s", channel, subject)
        return False
    try:
        import requests

        payload = {
            "channel": channel,
            "text": f"*{subject}*\n{body}",
            "username": "SENTINEL",
            "icon_emoji": ":warning:",
        }
        resp = requests.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        logger.info("[slack] Posted to %s: %s", channel, subject)
        return True
    except Exception as e:
        logger.warning("[slack] Failed to post to %s: %s", channel, e)
        return False


def _send_pagerduty(db: Session, subject: str, message: str, incident_id: Optional[str] = None) -> bool:
    config = _get_config(db, "pagerduty")
    routing_key = config.get("routing_key") or config.get("api_key")
    if not routing_key:
        logger.info("[pagerduty] Not configured — would trigger incident=%s title=%s", incident_id, subject)
        return False
    try:
        import requests

        payload = {
            "routing_key": routing_key,
            "event_action": "trigger",
            "payload": {
                "summary": subject[:120],
                "source": "sentinel",
                "severity": "critical",
                "custom_details": {"message": message[:500], "incident_id": incident_id},
            },
        }
        if incident_id:
            payload["dedup_key"] = f"sentinel-incident-{incident_id}"
        resp = requests.post("https://events.pagerduty.com/v2/enqueue", json=payload, timeout=10)
        resp.raise_for_status()
        logger.info("[pagerduty] Triggered: %s", subject)
        return True
    except Exception as e:
        logger.warning("[pagerduty] Failed: %s", e)
        return False
