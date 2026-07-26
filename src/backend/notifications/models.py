import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from src.backend.db import Base


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    channel = Column(String(50), nullable=False)  # email, slack, pagerduty
    enabled = Column(Boolean, nullable=False, default=True)
    config = Column(String(500), nullable=True)  # email address, slack channel, PD routing key
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
