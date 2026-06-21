"""Stub ORM models for shared tables referenced as FK targets in other modules.

These exist solely so SQLAlchemy's metadata knows about these tables when
building the SQLite test DB. Production uses the raw SQL migration in
schema/migrations/001_initial_schema.sql.
"""
import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.types import TypeDecorator

from src.backend.db import Base


class _UuidStr(TypeDecorator):
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return str(value) if value is not None else None

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        from uuid import UUID
        return UUID(value)


class TeamModel(Base):
    __tablename__ = "teams"
    id = Column(_UuidStr, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), nullable=True)


class UserModel(Base):
    __tablename__ = "users"
    id = Column(_UuidStr, primary_key=True, default=lambda: str(uuid.uuid4()))
    team_id = Column(_UuidStr, ForeignKey("teams.id", ondelete="CASCADE"), nullable=True)
    email = Column(String(255), nullable=False, unique=True)
    hashed_password = Column(String(255), nullable=False, default="")
    name = Column(String(255), nullable=False, default="")
    role = Column(String(50), nullable=False, default="VIEWER")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)


