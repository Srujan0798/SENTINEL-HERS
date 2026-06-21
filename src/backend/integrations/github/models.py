import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.types import JSON
from src.backend.db import Base


class Deployment(Base):
    __tablename__ = "deployments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    team_id = Column(String(36), nullable=False, index=True)
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True)
    service = Column(String(255), nullable=False)
    environment = Column(String(100), nullable=False, default="production")
    version = Column(String(255), nullable=True)
    sha = Column(String(40), nullable=True, index=True)
    status = Column(String(50), nullable=False, default="pending")
    source = Column(String(50), nullable=False, default="github")
    deployed_by = Column(String(255), nullable=True)
    deployed_at = Column(DateTime, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class Commit(Base):
    __tablename__ = "commits"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    team_id = Column(String(36), nullable=False, index=True)
    deployment_id = Column(String(36), ForeignKey("deployments.id", ondelete="SET NULL"), nullable=True)
    sha = Column(String(40), nullable=False, index=True)
    message = Column(Text, nullable=False, default="")
    author = Column(String(255), nullable=True)
    service = Column(String(255), nullable=True)
    branch = Column(String(255), nullable=True)
    source = Column(String(50), nullable=False, default="github")
    committed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
