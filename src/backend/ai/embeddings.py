import json
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

NV_EMBED_URL = "https://api.nvidia.com/v1/embeddings"
NV_EMBED_MODEL = "nvidia/nv-embed-v1"
EMBEDDING_DIM = 768


def _nvapi_key() -> str:
    return os.getenv("NVAPI_KEY", "")


def generate_embedding(text: str) -> list[float] | None:
    key = _nvapi_key()
    if not key:
        logger.warning("NVAPI_KEY not set — cannot generate embeddings")
        return None
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                NV_EMBED_URL,
                headers={"Authorization": f"Bearer {key}"},
                json={"model": NV_EMBED_MODEL, "input": text[:8000]},
            )
            resp.raise_for_status()
            data = resp.json()
            return data["data"][0]["embedding"]
    except Exception as e:
        logger.error("Embedding generation failed: %s", e)
        return None


def embed_recent_logs(db_session, team_id: str, limit: int = 100) -> int:
    from src.backend.ai.embeddings_model import LogEmbedding
    from src.backend.logs.models import LogEntryModel

    logs = (
        db_session.query(LogEntryModel)
        .filter(LogEntryModel.team_id == team_id)
        .order_by(LogEntryModel.created_at.desc())
        .limit(limit)
        .all()
    )
    count = 0
    for log in logs:
        existing = db_session.query(LogEmbedding).filter_by(log_id=str(log.id)).first()
        if existing:
            continue
        text = f"{log.service} {log.level} {log.message}"
        embedding = generate_embedding(text)
        if embedding:
            db_session.add(LogEmbedding(log_id=str(log.id), team_id=str(log.team_id), embedding=embedding))
            count += 1
            if count % 10 == 0:
                db_session.commit()
    if count > 0:
        db_session.commit()
    return count


def search_similar_logs(query: str, team_id: str, db_session, top_k: int = 20) -> list[dict[str, Any]]:
    from sqlalchemy import text

    query_embedding = generate_embedding(query)
    if not query_embedding:
        return []

    embedding_json = json.dumps(query_embedding)
    sql = text("""
        SELECT log_id, (embedding <=> :embedding::vector) AS distance
        FROM log_embeddings
        WHERE team_id = :team_id
        ORDER BY distance ASC
        LIMIT :top_k
    """)
    rows = db_session.execute(sql, {"embedding": embedding_json, "team_id": team_id, "top_k": top_k}).fetchall()
    if not rows:
        return []

    from src.backend.logs.models import LogEntryModel

    log_ids = [str(row[0]) for row in rows]
    logs = db_session.query(LogEntryModel).filter(LogEntryModel.id.in_(log_ids)).all()
    log_map = {str(log.id): log for log in logs}

    results = []
    for row in rows:
        log_id = str(row[0])
        distance = float(row[1])
        log = log_map.get(log_id)
        if log:
            similarity = max(0.0, 1.0 - distance)
            results.append({
                "id": log_id,
                "team_id": str(log.team_id),
                "service": log.service,
                "level": log.level,
                "message": log.message,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "_score": round(similarity, 4),
            })
    return results
