"""Parse transcribed voice text into a structured incident via LLM."""
import json
import re
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
    if not text or not text.strip():
        raise ValueError("Transcription is empty — cannot parse incident from empty text")

    if provider is None:
        provider = get_provider()

    try:
        response = provider.complete(
            messages=[{"role": "user", "content": f"Parse this SRE voice note:\n\n{text}"}],
            system=PARSE_SYSTEM_PROMPT,
        )
    except Exception as exc:
        raise ValueError(f"LLM parse call failed: {exc}") from exc

    clean = response.strip()
    if clean.startswith("[mock-ai]"):
        return _fallback_parse(text)

    try:
        data = json.loads(clean)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", clean, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError:
                return _fallback_parse(text)
        else:
            return _fallback_parse(text)

    try:
        parsed = ParsedIncident(**data)
    except Exception as exc:
        raise ValueError(f"Parsed data did not match required schema: {exc}") from exc

    if not parsed.title.strip():
        raise ValueError("Parse produced an empty title — transcript may be incoherent")

    return parsed


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
