"""AI root-cause analysis — returns ranked hypotheses with confidence scores."""
import json
import re
from typing import Any

from src.backend.ai.provider import get_provider


class RootCauseSuggestion:
    def __init__(
        self,
        hypothesis: str,
        confidence: float,
        supporting_evidence: list[str],
        suggested_action: str,
    ):
        self.hypothesis = hypothesis
        self.confidence = max(0.0, min(1.0, confidence))
        self.supporting_evidence = supporting_evidence
        self.suggested_action = suggested_action

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis": self.hypothesis,
            "confidence": self.confidence,
            "supporting_evidence": self.supporting_evidence,
            "suggested_action": self.suggested_action,
        }


def suggest_root_causes(
    incident: dict[str, Any],
    logs: list[dict[str, Any]],
    deployments: list[dict[str, Any]] | None = None,
) -> list[RootCauseSuggestion]:
    log_sample = "\n".join(
        f"[{e.get('level','info').upper()}] {e.get('service','?')}: {e.get('message','')}"
        for e in logs[:30]
    )
    deploy_sample = "\n".join(
        f"- {d.get('service','?')} deployed {d.get('version','?')} at {d.get('deployed_at','?')}"
        for d in (deployments or [])[:5]
    )

    system = (
        "You are an expert SRE performing root cause analysis. "
        "Return ONLY valid JSON — a list of root cause hypotheses, ranked by confidence descending."
    )
    user_msg = f"""Analyze this incident and return up to 5 root cause hypotheses as JSON.

Incident: {incident.get('title')} (severity={incident.get('severity')}, status={incident.get('status')})

Logs ({len(logs)} total, showing up to 30):
{log_sample or '(none)'}

Recent deployments:
{deploy_sample or '(none)'}

Return JSON array (max 5 items), each object with exactly these keys:
  "hypothesis": string (what likely caused the incident)
  "confidence": float 0.0-1.0 (your confidence)
  "supporting_evidence": array of strings (specific log lines or facts)
  "suggested_action": string (concrete remediation step)

JSON only, no other text:"""

    provider = get_provider()
    raw = provider.complete([{"role": "user", "content": user_msg}], system=system)

    # Parse JSON — be lenient
    try:
        # Strip markdown fences and any trailing text
        raw_clean = raw.strip()
        if "```" in raw_clean:
            raw_clean = re.sub(r"^```(?:json)?\s*", "", raw_clean)
            raw_clean = re.sub(r"```[\s\S]*$", "", raw_clean)
            raw_clean = raw_clean.strip()
        items = json.loads(raw_clean)
        if items is None:
            items = []
        if not isinstance(items, list):
            items = [items]
    except (json.JSONDecodeError, ValueError):
        # Fallback: return single low-confidence suggestion
        items = [{
            "hypothesis": "Unable to determine root cause from available data.",
            "confidence": 0.1,
            "supporting_evidence": [raw[:200]],
            "suggested_action": "Gather more logs and re-run analysis.",
        }]

    results = []
    for item in items[:5]:
        if isinstance(item, dict):
            hypothesis = item.get("hypothesis")
            confidence_raw = item.get("confidence")
            evidence_raw = item.get("supporting_evidence")
            action_raw = item.get("suggested_action")
            try:
                confidence = float(confidence_raw) if confidence_raw is not None else 0.5
            except (TypeError, ValueError):
                confidence = 0.5
            if isinstance(evidence_raw, list):
                supporting_evidence = [str(e) for e in evidence_raw]
            elif isinstance(evidence_raw, str):
                supporting_evidence = [evidence_raw]
            else:
                supporting_evidence = []
            results.append(RootCauseSuggestion(
                hypothesis=str(hypothesis) if hypothesis else "",
                confidence=confidence,
                supporting_evidence=supporting_evidence,
                suggested_action=str(action_raw) if action_raw else "",
            ))

    return sorted(results, key=lambda x: x.confidence, reverse=True)
