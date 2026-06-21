"""Auto-generate structured postmortem reports from resolved incident data."""
from typing import Any

from src.backend.ai.provider import get_provider

POSTMORTEM_SECTIONS = [
    "Executive Summary",
    "Timeline",
    "Root Cause Analysis",
    "Impact Assessment",
    "Resolution Steps",
    "Action Items",
]


class PostmortemReport:
    def __init__(self, incident_id: str, content: str, sections: dict[str, str]):
        self.incident_id = incident_id
        self.content = content
        self.sections = sections

    def to_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "content": self.content,
            "sections": self.sections,
        }


def generate_postmortem(
    incident: dict[str, Any],
    timeline_events: list[dict[str, Any]],
    root_causes: list[dict[str, Any]] | None = None,
    tasks: list[dict[str, Any]] | None = None,
) -> PostmortemReport:
    timeline_text = "\n".join(
        f"  {e.get('ts','?')} [{e.get('event_type','?')}] by {e.get('actor','?')}: {e.get('description','')}"
        for e in timeline_events
    ) or "  (no timeline events recorded)"

    root_cause_text = "\n".join(
        f"  {i+1}. {rc.get('hypothesis','')} (confidence={rc.get('confidence',0):.0%}): {rc.get('suggested_action','')}"
        for i, rc in enumerate(root_causes or [])
    ) or "  (root cause analysis not available)"

    system = (
        "You are an expert SRE writing a postmortem report. "
        "Be concise, factual, and actionable. Use markdown formatting."
    )

    user_msg = f"""Write a complete postmortem for this resolved incident.

Incident:
  Title: {incident.get('title')}
  Severity: {incident.get('severity')}
  Status: {incident.get('status')}
  Detected: {incident.get('detected_at')}
  Resolved: {incident.get('resolved_at', 'N/A')}

Timeline:
{timeline_text}

Root Cause Analysis:
{root_cause_text}

Write the postmortem with ALL 6 sections using markdown headers (## Section Name):
1. ## Executive Summary (2 sentences)
2. ## Timeline (chronological, from detected to resolved)
3. ## Root Cause Analysis (top causes with evidence)
4. ## Impact Assessment (services, duration, users)
5. ## Resolution Steps (what was done to fix it)
6. ## Action Items (exactly 5 specific preventive actions)

Postmortem:"""

    provider = get_provider()
    content = provider.complete([{"role": "user", "content": user_msg}], system=system)

    # Extract sections from markdown
    sections: dict[str, str] = {}
    import re
    pattern = r"##\s+(.+?)\n(.*?)(?=##|\Z)"
    for match in re.finditer(pattern, content, re.DOTALL):
        title = match.group(1).strip()
        body = match.group(2).strip()
        sections[title] = body

    return PostmortemReport(
        incident_id=str(incident.get("id", "")),
        content=content,
        sections=sections,
    )
