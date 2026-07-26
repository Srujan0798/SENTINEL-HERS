from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, String, DateTime, ForeignKey, func

from src.backend.db import Base
from src.backend.shared_models import _UuidStr


class LogEmbedding(Base):
    __tablename__ = "log_embeddings"

    log_id = Column(_UuidStr, ForeignKey("log_entries.id", ondelete="CASCADE"), primary_key=True)
    team_id = Column(_UuidStr, nullable=False, index=True)
    embedding = Column(Vector(768))
    model = Column(String(100), nullable=False, default="nvidia/nv-embed-v1")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
