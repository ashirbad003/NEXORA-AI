import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, Table, Text, Integer, Float, Index
)
from sqlalchemy.orm import relationship
from backend.app.db.session import Base

class LearningModule(Base):
    """
    Curriculum module / topic entity for the Interactive Concept Explorer (FEAT-123..FEAT-144).
    Covers DSA and Core CS Modules (OS, DBMS, CN, OOPS).
    """
    __tablename__ = "learning_modules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    slug = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False, index=True)  # DSA, OS, DBMS, CN, OOPS
    summary = Column(Text, nullable=False)
    content_markdown = Column(Text, nullable=False)
    estimated_read_time_minutes = Column(Integer, default=5, nullable=False)
    difficulty_level = Column(String(20), default="Medium", nullable=False)  # Easy, Medium, Hard
    prerequisites = Column(Text, nullable=True)  # JSON or comma-separated module slugs
    order_index = Column(Integer, default=0, nullable=False, index=True)
    is_published = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    progress_records = relationship("StudentTopicProgress", back_populates="module", cascade="all, delete-orphan")
    notes = relationship("StudentTopicNote", back_populates="module", cascade="all, delete-orphan")

class StudentTopicProgress(Base):
    """
    Per-student topic mastery & completion tracker (FEAT-128).
    Strictly isolated per user_id.
    """
    __tablename__ = "student_topic_progress"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id = Column(String(36), ForeignKey("learning_modules.id", ondelete="CASCADE"), nullable=False, index=True)
    is_completed = Column(Boolean, default=False, nullable=False)
    mastery_score = Column(Integer, default=0, nullable=False)  # 0 to 100
    last_studied_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    module = relationship("LearningModule", back_populates="progress_records")

    __table_args__ = (
        Index("ix_student_topic_progress_user_module", "user_id", "module_id", unique=True),
    )

class StudentTopicNote(Base):
    """
    Student bookmarking & personal notes drawer (FEAT-141).
    Anchored to learning topics. Strictly user-isolated (IDOR protected).
    """
    __tablename__ = "student_topic_notes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id = Column(String(36), ForeignKey("learning_modules.id", ondelete="CASCADE"), nullable=False, index=True)
    note_content = Column(Text, nullable=False)
    is_bookmarked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    module = relationship("LearningModule", back_populates="notes")

class TopicFeedback(Base):
    """
    Topic difficulty rating and confusing section feedback (FEAT-135).
    """
    __tablename__ = "topic_feedback"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    module_id = Column(String(36), ForeignKey("learning_modules.id", ondelete="CASCADE"), nullable=False, index=True)
    difficulty_rating = Column(Integer, nullable=False)  # 1 (Very Easy) to 5 (Very Hard)
    confusing_sections = Column(Text, nullable=True)
    feedback_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    module = relationship("LearningModule")

