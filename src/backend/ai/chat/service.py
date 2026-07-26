"""RAG-based conversational AI for querying incidents and logs.
Uses relevance scoring to retrieve the most contextually relevant logs.
"""
import re
from typing import Any

from src.backend.ai.provider import get_provider


class Citation:
    def __init__(self, type_: str, id_: str, excerpt: str, score: float = 1.0):
        self.type = type_
        self.id = id_
        self.excerpt = excerpt
        self.score = score

    def to_dict(self) -> dict:
        return {"type": self.type, "id": self.id, "excerpt": self.excerpt, "score": self.score}


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


def _tokenize(text: str) -> set[str]:
    """Extract meaningful keywords from text."""
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9]{2,}", text.lower())
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "dare", "ought",
        "used", "this", "that", "these", "those", "what", "which", "who",
        "whom", "where", "when", "why", "how", "all", "each", "every",
        "both", "few", "more", "most", "other", "some", "such", "no", "nor",
        "not", "only", "own", "same", "so", "than", "too", "very", "just",
        "about", "above", "after", "again", "against", "below", "between",
        "into", "through", "during", "before", "after", "from", "with",
        "without", "and", "but", "or", "for", "nor", "yet", "because",
        "error", "log", "incident", "please", "tell", "show", "find",
    }
    return {w for w in words if w not in stopwords}


def _score_relevance(log: dict, query_tokens: set[str]) -> float:
    """Score log relevance to query using keyword overlap + level boost."""
    if not query_tokens:
        return 0.0
    text = f"{log.get('message', '')} {log.get('service', '')}".lower()
    log_tokens = set(re.findall(r"[a-zA-Z][a-zA-Z0-9]{2,}", text))
    if not log_tokens:
        return 0.0
    overlap = len(query_tokens & log_tokens)
    score = overlap / max(len(query_tokens), 1)
    level_boost = {"critical": 1.5, "error": 1.3, "warn": 1.1, "info": 0.8}.get(
        log.get("level", "").lower(), 1.0
    )
    return round(score * level_boost, 4)


def _rerank_logs(logs: list[dict], query: str) -> list[dict]:
    """Rerank logs by relevance to the user's query."""
    tokens = _tokenize(query)
    scored = [(log, _score_relevance(log, tokens)) for log in logs]
    scored.sort(key=lambda x: -x[1])
    return [s[0] for s in scored if s[1] > 0]


def _build_context(
    incidents: list[dict], logs: list[dict], query: str = ""
) -> tuple[str, list[Citation]]:
    citations: list[Citation] = []
    parts: list[str] = []

    for inc in incidents[:5]:
        excerpt = f"Incident {inc.get('id','')} [{inc.get('severity','?')}]: {inc.get('title','')} — status: {inc.get('status','?')}"
        parts.append(f"[incident:{inc.get('id','')}] {excerpt}")
        citations.append(Citation("incident", str(inc.get("id", "")), excerpt, 1.0))

    reranked = _rerank_logs(logs, query) if query else logs
    for log in reranked[:20]:
        excerpt = f"[{log.get('level','?').upper()}] {log.get('service','?')}: {log.get('message','')}"
        parts.append(f"[log:{log.get('id','')}] {excerpt}")
        citations.append(Citation("log", str(log.get("id", "")), excerpt[:120], log.get("_score", 1.0)))

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

    context, citations = _build_context(incidents, logs, query=user_message)

    if not context:
        return ChatResponse(
            answer="I don't have enough data to answer that. Try narrowing the time range or checking that logs are being ingested.",
            citations=[],
            confidence=0.0,
        )

    confidence = 0.0
    if len(incidents) > 0:
        confidence += 0.3
    if citations:
        confidence += 0.3 * min(1.0, len([c for c in citations if c.score > 0]) / 3)

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

    cited_ids = set(re.findall(r"\[(log|incident):([^\]]+)\]", answer))
    used_citations = [c for c in citations if (c.type, c.id) in cited_ids] or citations[:3]

    return ChatResponse(answer=answer, citations=used_citations, confidence=min(confidence + 0.5, 1.0))
