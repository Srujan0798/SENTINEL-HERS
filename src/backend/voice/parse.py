"""Parse transcribed voice text into a structured incident via LLM."""
import json
from typing import Literal

from pydantic import BaseModel, Field

from src.backend.ai.provider import AIProvider, get_provider

PARSE_SYSTEM_PROMPT = (
    "You are an SRE incident parser. Given a voice transcription of an incident report, "
    "extract a structured incident. Return ONLY valid JSON with these fields:\n"
    '- "title": short incident title (max 100 chars)\n'
    '- "description": detailed description of what happened\n'
    '- "severity": one of "SEV1", "SEV2", "SEV3", "SEV4"\n'
    '- "affected_services": list of service names mentioned\n\n'
    "Rules:\n"
    "- SEV1: complete outage or data loss\n"
    "- SEV2: major degradation affecting many users\n"
    "- SEV3: partial impact, workaround available\n"
    "- SEV4: minor, no user impact\n"
    "Return ONLY the JSON object, no markdown fences."
)


class ParsedIncident(BaseModel):
    title: str = Field(..., max_length=500)
    description: str
    severity: Literal["SEV1", "SEV2", "SEV3", "SEV4"]
    affected_services: list[str] = []


def parse_voice_to_incident(text: str, provider: AIProvider | None = None) -> ParsedIncident:
    """Use LLM to parse transcribed text into a structured incident."""
    if provider is None:
        provider = get_provider()

    response = provider.complete(
        messages=[{"role": "user", "content": f"Parse this SRE voice note:\n\n{text}"}],
        system=PARSE_SYSTEM_PROMPT,
    )

    # Handle mock provider prefix
    clean = response.strip()
    if clean.startswith("[mock-ai]"):
        # Mock provider returns a prefixed string; fall back to deterministic parse
        return _fallback_parse(text)

    try:
        data = json.loads(clean)
    except json.JSONDecodeError:
        # Try to extract JSON from response (handle markdown fences)
        import re
        match = re.search(r"\{.*\}", clean, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            return _fallback_parse(text)

    return ParsedIncident(**data)


def _fallback_parse(text: str) -> ParsedIncident:
    """Deterministic fallback when LLM doesn't return valid JSON."""
    severity = "SEV3"
    lower = text.lower()
    if any(w in lower for w in ["down", "outage", "data loss", "on fire", "completely"]):
        severity = "SEV1"
    elif any(w in lower for w in ["major", "degradation", "slow", "timeout"]):
        severity = "SEV2"
    elif any(w in lower for w in ["minor", "cosmetic", "small"]):
        severity = "SEV4"

    services = []
    for svc in ["payments", "auth", "api", "database", "cache", "gateway", "frontend", "backend"]:
        if svc in lower:
            services.append(svc)

    title = text[:100].strip()
    if len(text) > 100:
        title = title.rsplit(" ", 1)[0] + "..."

    return ParsedIncident(
        title=title,
        description=text,
        severity=severity,
        affected_services=services,
    )
