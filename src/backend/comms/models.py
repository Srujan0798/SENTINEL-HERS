"""ORM models for incident comms — channels, members, messages."""
import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, func, JSON

from src.backend.db import Base


class Channel(Base):
    """One chat channel per incident. Auto-created with the incident."""
    __tablename__ = "channels"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    team_id = Column(String(36), nullable=False, index=True)
    incident_id = Column(
        String(36),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    name = Column(String(255), nullable=False)
    topic = Column(String(500), nullable=True)
    is_archived = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class ChannelMember(Base):
    """Track which users have joined a channel (for @mention lookups)."""
    __tablename__ = "channel_members"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    team_id = Column(String(36), nullable=False, index=True)
    channel_id = Column(
        String(36),
        ForeignKey("channels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(String(36), nullable=False, index=True)
    user_name = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default="member")
    joined_at = Column(DateTime, nullable=False, server_default=func.now())


class Message(Base):
    """A single chat message. May be posted by a user OR by the AI."""
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    team_id = Column(String(36), nullable=False, index=True)
    channel_id = Column(
        String(36),
        ForeignKey("channels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    incident_id = Column(
        String(36),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_id = Column(String(36), nullable=True)
    author_name = Column(String(255), nullable=True)
    author_type = Column(String(20), nullable=False, default="user")
    body = Column(Text, nullable=False)
    mentions = Column(JSON, nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)
    edited_at = Column(DateTime, nullable=True)
