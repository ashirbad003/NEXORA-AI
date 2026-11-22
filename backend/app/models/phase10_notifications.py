import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, Text, Integer, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from backend.app.db.session import Base

class UserNotification(Base):
    __tablename__ = "user_notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(50), nullable=False, default="GENERAL", index=True)  # REVISION, COMMUNITY, SYSTEM, PLACEMENT
    urgency = Column(String(20), nullable=False, default="NORMAL")  # LOW, NORMAL, HIGH, CRITICAL
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    action_url = Column(String(500), nullable=True)
    payload = Column(JSONB, nullable=False, default=dict)
    is_read = Column(Boolean, nullable=False, default=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    __table_args__ = (
        Index("ix_user_notifications_user_unread", "user_id", "is_read", "created_at"),
    )

    user = relationship("User", foreign_keys=[user_id])


class UserNotificationPreference(Base):
    __tablename__ = "user_notification_preferences"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    in_app_enabled = Column(Boolean, nullable=False, default=True)
    email_enabled = Column(Boolean, nullable=False, default=True)
    push_enabled = Column(Boolean, nullable=False, default=False)
    category_overrides = Column(JSONB, nullable=False, default=dict)  # {"REVISION": {"email": false}}
    quiet_hours_start = Column(String(5), nullable=True)  # e.g. "22:00"
    quiet_hours_end = Column(String(5), nullable=True)    # e.g. "07:00"
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", foreign_keys=[user_id])
