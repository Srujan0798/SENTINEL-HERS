"""SLA policy: per-severity response time limits in minutes."""

SLA_MINUTES: dict[str, int] = {
    "SEV1": 15,
    "SEV2": 60,
    "SEV3": 240,
    "SEV4": 1440,
}


def sla_minutes_for(severity: str) -> int:
    return SLA_MINUTES.get(str(severity).upper(), 240)


def time_remaining_minutes(detected_at, severity: str) -> float:
    """Return minutes remaining until SLA breach (negative = already breached)."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    if detected_at.tzinfo is None:
        import pytz
        detected_at = pytz.utc.localize(detected_at)
    elapsed = (now - detected_at).total_seconds() / 60
    return sla_minutes_for(severity) - elapsed
