import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, Text, Integer, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from backend.app.db.session import Base

class PeerDiscussionThread(Base):
    __tablename__ = "peer_discussion_threads"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, default="General", index=True)
    context_type = Column(String(50), nullable=True)  # 'problem', 'topic', 'assessment', 'general'
    context_id = Column(String(100), nullable=True, index=True)
    upvotes = Column(Integer, nullable=False, default=0)
    reply_count = Column(Integer, nullable=False, default=0)
    is_resolved = Column(Boolean, nullable=False, default=False, index=True)
    status = Column(String(30), nullable=False, default="OPEN")  # 'OPEN', 'RESOLVED', 'CLOSED', 'FLAGGED'
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    replies = relationship("PeerDiscussionReply", back_populates="thread", cascade="all, delete-orphan", order_by="PeerDiscussionReply.created_at")


class PeerDiscussionReply(Base):
    __tablename__ = "peer_discussion_replies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    thread_id = Column(String(36), ForeignKey("peer_discussion_threads.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    code_snippet = Column(Text, nullable=True)
    upvotes = Column(Integer, nullable=False, default=0)
    is_accepted = Column(Boolean, nullable=False, default=False, index=True)
    status = Column(String(30), nullable=False, default="ACTIVE")  # 'ACTIVE', 'FLAGGED', 'HIDDEN'
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    thread = relationship("PeerDiscussionThread", back_populates="replies")
    user = relationship("User", foreign_keys=[user_id])


class PeerStudyGroup(Base):
    __tablename__ = "peer_study_groups"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    creator_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    goal_description = Column(String(255), nullable=True)
    is_private = Column(Boolean, nullable=False, default=False)
    invite_code = Column(String(32), unique=True, nullable=True, index=True)
    member_count = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    creator = relationship("User", foreign_keys=[creator_id])
    members = relationship("PeerStudyGroupMember", back_populates="group", cascade="all, delete-orphan")


class PeerStudyGroupMember(Base):
    __tablename__ = "peer_study_group_members"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    group_id = Column(String(36), ForeignKey("peer_study_groups.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(30), nullable=False, default="MEMBER")  # 'ADMIN', 'MEMBER'
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_study_group_members_group_user"),
    )

    group = relationship("PeerStudyGroup", back_populates="members")
    user = relationship("User", foreign_keys=[user_id])
