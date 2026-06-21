"""RAG-based conversational AI for querying incidents and logs."""
import re
from typing import Any

from src.backend.ai.provider import get_provider


class Citation:
    def __init__(self, type_: str, id_: str, excerpt: str):
        self.type = type_
        self.id = id_
        self.excerpt = excerpt

    def to_dict(self) -> dict:
        return {"type": self.type, "id": self.id, "excerpt": self.excerpt}


class ChatResponse:
    def __init__(self, answer: str, citations: list[Citation], confidence: float):
        self.answer = answer
        self.citations = citations
        self.confidence = confidence

    def to_dict(self) -> dict:
        return {
            "answer": self.answer,
            "citations": [c.to_dict() for c in self.citations],
            "confidence": self.confidence,
        }


def _build_context(incidents: list[dict], logs: list[dict]) -> tuple[str, list[Citation]]:
    citations: list[Citation] = []
    parts: list[str] = []

    for inc in incidents[:5]:
        excerpt = f"Incident {inc.get('id','')} [{inc.get('severity','?')}]: {inc.get('title','')} — status: {inc.get('status','?')}"
        parts.append(f"[incident:{inc.get('id','')}] {excerpt}")
        citations.append(Citation("incident", str(inc.get("id", "")), excerpt))

    for log in logs[:20]:
        excerpt = f"[{log.get('level','?').upper()}] {log.get('service','?')}: {log.get('message','')}"
        parts.append(f"[log:{log.get('id','')}] {excerpt}")
        citations.append(Citation("log", str(log.get("id", "")), excerpt[:120]))

    return "\n".join(parts), citations


def chat(
    team_id: str,
    user_message: str,
    history: list[dict[str, str]],
    incidents: list[dict[str, Any]] | None = None,
    logs: list[dict[str, Any]] | None = None,
) -> ChatResponse:
    incidents = incidents or []
    logs = logs or []

    context, citations = _build_context(incidents, logs)

    if not context:
        return ChatResponse(
            answer="I don't have enough data to answer that. Try narrowing the time range or checking that logs are being ingested.",
            citations=[],
            confidence=0.0,
        )

    system = (
        "You are SENTINEL, an incident operations assistant. "
        "Answer ONLY from the provided context. "
        "Cite evidence with [log:id] or [incident:id] markers. "
        "If context is insufficient, say so explicitly — never hallucinate."
    )

    messages = list(history)
    messages.append({
        "role": "user",
        "content": f"Context:\n{context}\n\nQuestion: {user_message}",
    })

    provider = get_provider()
    answer = provider.complete(messages, system=system)

    # Extract cited IDs from the answer
    cited_ids = set(re.findall(r"\[(log|incident):([^\]]+)\]", answer))
    used_citations = [c for c in citations if (c.type, c.id) in cited_ids] or citations[:3]

    confidence = 0.8 if used_citations else 0.3

    return ChatResponse(answer=answer, citations=used_citations, confidence=confidence)
