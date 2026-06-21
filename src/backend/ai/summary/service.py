"""AI incident summary generation with Redis cache."""
import json
import os
from typing import Any

from src.backend.ai.provider import get_provider


CACHE_TTL = 300  # 5 min


def _redis():
    try:
        import redis
        url = os.getenv("REDIS_URL", "")
        if not url:
            return None
        return redis.from_url(url, decode_responses=True)
    except Exception:
        return None


def generate_incident_summary(
    incident: dict[str, Any],
    logs: list[dict[str, Any]],
    alerts: list[dict[str, Any]],
) -> str:
    cache_key = f"sentinel:ai:summary:{incident['id']}"
    r = _redis()
    if r:
        cached = r.get(cache_key)
        if cached:
            return cached

    log_sample = "\n".join(
        f"[{e.get('level','info').upper()}] {e.get('service','?')}: {e.get('message','')}"
        for e in logs[:20]
    )
    alert_sample = "\n".join(
        f"- {a.get('title','?')} (severity={a.get('severity','?')})"
        for a in alerts[:10]
    )

    system = (
        "You are SENTINEL, an expert SRE incident analyst. "
        "Write concise, factual incident summaries from operational data."
    )
    user_msg = f"""Summarize this incident in exactly 3 paragraphs:
1. What happened and when
2. Impact on services/users
3. Current status and next steps

Incident:
  ID: {incident.get('id')}
  Title: {incident.get('title')}
  Severity: {incident.get('severity')}
  Status: {incident.get('status')}
  Detected at: {incident.get('detected_at')}

Recent logs ({len(logs)} total, showing first 20):
{log_sample or '(none)'}

Alerts:
{alert_sample or '(none)'}

Write the 3-paragraph summary now:"""

    provider = get_provider()
    summary = provider.complete([{"role": "user", "content": user_msg}], system=system)

    if r:
        try:
            r.setex(cache_key, CACHE_TTL, summary)
        except Exception:
            pass

    return summary
