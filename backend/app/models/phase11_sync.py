import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, UniqueConstraint, Index, BigInteger
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from backend.app.models.auth import Base


class MobileDeviceToken(Base):
    """
    Tracks registered mobile devices and Expo push notification endpoints.
    Enforces atomic upsert on (user_id, device_id).
    """
    __tablename__ = "mobile_device_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(String(100), nullable=False)
    expo_push_token = Column(String(255), nullable=False)
    device_os = Column(String(32), nullable=False, default="ANDROID")
    device_model = Column(String(100), nullable=True)
    app_version = Column(String(32), nullable=False, default="1.0.0")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_used_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "device_id", name="uq_mobile_device_user_device"),
        Index("ix_mobile_device_user_active", "user_id", "is_active"),
        Index("ix_mobile_device_expo_token", "expo_push_token"),
    )

    user = relationship("User", foreign_keys=[user_id])


class UserSyncCounter(Base):
    """
    Global per-user monotonic sequence counter and retention threshold.
    One row per student. Locked with SELECT FOR UPDATE during domain mutations.
    """
    __tablename__ = "user_sync_counters"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    current_val = Column(BigInteger, nullable=False, default=0)
    min_available_seq = Column(BigInteger, nullable=False, default=1)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", foreign_keys=[user_id])


class UserSyncWatermark(Base):
    """
    Device-level synchronization acknowledgment state.
    One row per user per physical device. Never allocates global sequences.
    """
    __tablename__ = "user_sync_watermarks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_id = Column(String(100), nullable=False)
    last_acknowledged_seq = Column(BigInteger, nullable=False, default=0)
    last_synced_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    client_app_version = Column(String(32), nullable=False, default="1.0.0")

    __table_args__ = (
        UniqueConstraint("user_id", "device_id", name="uq_sync_watermarks_user_device"),
        Index("ix_sync_watermarks_user_synced", "user_id", "last_synced_at"),
    )

    user = relationship("User", foreign_keys=[user_id])


class UserSyncChangeFeed(Base):
    """
    Durable append-only change ledger per student.
    Inserted in the exact same database transaction as domain mutations.
    """
    __tablename__ = "user_sync_change_feed"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    change_seq = Column(BigInteger, nullable=False)
    entity_type = Column(String(50), nullable=False)  # "CARD_REVIEW", "FLASHCARD_DECK", "FLASHCARD_ITEM", "MISTAKE_ENTRY"
    entity_id = Column(String(36), nullable=False)
    operation = Column(String(20), nullable=False)  # "UPSERT", "DELETE"
    payload = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "change_seq", name="uq_change_feed_user_seq"),
        Index("ix_change_feed_user_seq", "user_id", "change_seq"),
    )

    user = relationship("User", foreign_keys=[user_id])


class UserSyncTombstone(Base):
    """
    Sequence-based deletion ledger supporting repeated Create -> Delete -> Restore -> Delete cycles.
    """
    __tablename__ = "user_sync_tombstones"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)  # "FLASHCARD_DECK", "FLASHCARD_ITEM", "MISTAKE_ENTRY"
    entity_id = Column(String(36), nullable=False)
    change_seq = Column(BigInteger, nullable=False)
    deleted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "change_seq", name="uq_tombstones_user_seq"),
        Index("ix_tombstones_user_entity", "user_id", "entity_type", "entity_id"),
        Index("ix_tombstones_deleted_at", "deleted_at"),
    )

    user = relationship("User", foreign_keys=[user_id])
