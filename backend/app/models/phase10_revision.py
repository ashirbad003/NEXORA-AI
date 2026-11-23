import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, Text, Integer, Float, Index, UniqueConstraint, BigInteger
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from backend.app.db.session import Base

class FlashcardDeck(Base):
    __tablename__ = "flashcard_decks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, default="General", index=True)
    tags = Column(JSONB, nullable=False, default=list)
    is_public = Column(Boolean, nullable=False, default=False, index=True)
    is_system = Column(Boolean, nullable=False, default=False)
    is_approved = Column(Boolean, nullable=False, default=False, index=True)
    is_archived = Column(Boolean, nullable=False, default=False)
    share_slug = Column(String(100), unique=True, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    cards = relationship("FlashcardItem", back_populates="deck", cascade="all, delete-orphan", order_by="FlashcardItem.order_index")
    user = relationship("User", foreign_keys=[user_id])


class FlashcardItem(Base):
    __tablename__ = "flashcard_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    deck_id = Column(String(36), ForeignKey("flashcard_decks.id", ondelete="CASCADE"), nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    code_snippet = Column(Text, nullable=True)
    audio_url = Column(String(500), nullable=True)
    order_index = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    deck = relationship("FlashcardDeck", back_populates="cards")
    reviews = relationship("StudentCardReview", back_populates="card", cascade="all, delete-orphan")


class StudentCardReview(Base):
    __tablename__ = "student_card_reviews"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    card_id = Column(String(36), ForeignKey("flashcard_items.id", ondelete="CASCADE"), nullable=False, index=True)
    repetition = Column(Integer, nullable=False, default=0)
    interval_days = Column(Integer, nullable=False, default=0)
    ease_factor = Column(Float, nullable=False, default=2.50)
    stability = Column(Float, nullable=False, default=1.00)
    next_review_at = Column(DateTime(timezone=True), nullable=False, index=True)
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    state_version = Column(BigInteger, nullable=False, default=1)

    __table_args__ = (
        UniqueConstraint("user_id", "card_id", name="uq_student_card_reviews_user_card"),
        Index("ix_student_card_reviews_user_next_review", "user_id", "next_review_at"),
    )

    card = relationship("FlashcardItem", back_populates="reviews")
    user = relationship("User", foreign_keys=[user_id])


class StudentCardReviewLog(Base):
    __tablename__ = "student_card_review_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    card_id = Column(String(36), ForeignKey("flashcard_items.id", ondelete="SET NULL"), nullable=True, index=True)
    review_id = Column(String(36), ForeignKey("student_card_reviews.id", ondelete="SET NULL"), nullable=True)
    session_id = Column(String(36), ForeignKey("revision_focus_sessions.id", ondelete="SET NULL"), nullable=True)
    
    idempotency_key = Column(String(64), nullable=False)
    request_hash = Column(String(64), nullable=False)
    submitted_grade = Column(Integer, nullable=False)
    time_spent_ms = Column(Integer, nullable=False, default=0)

    prev_repetition = Column(Integer, nullable=False)
    new_repetition = Column(Integer, nullable=False)
    prev_interval = Column(Integer, nullable=False)
    new_interval = Column(Integer, nullable=False)
    prev_ease_factor = Column(Float, nullable=False)
    new_ease_factor = Column(Float, nullable=False)
    prev_stability = Column(Float, nullable=False)
    new_stability = Column(Float, nullable=False)
    prev_next_review_at = Column(DateTime(timezone=True), nullable=True)
    new_next_review_at = Column(DateTime(timezone=True), nullable=False)

    response_payload = Column(JSONB, nullable=False)
    reviewed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    client_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    device_id = Column(String(100), nullable=True)
    is_superseded = Column(Boolean, nullable=False, default=False)
    base_state_version = Column(BigInteger, nullable=True)
    resulting_state_version = Column(BigInteger, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_review_logs_user_idempotency"),
        Index("ix_review_logs_user_reviewed_at", "user_id", "reviewed_at"),
    )

    user = relationship("User", foreign_keys=[user_id])


class MistakeNotebookEntry(Base):
    __tablename__ = "mistake_notebook_entries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    source_type = Column(String(50), nullable=False, default="manual")  # 'coding', 'assessment', 'manual'
    source_id = Column(String(100), nullable=True)
    title = Column(String(255), nullable=False)
    question_context = Column(Text, nullable=True)
    submitted_answer = Column(Text, nullable=True)
    expected_answer = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    tags = Column(JSONB, nullable=False, default=list)
    is_resolved = Column(Boolean, nullable=False, default=False, index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", foreign_keys=[user_id])


class RevisionFocusSession(Base):
    __tablename__ = "revision_focus_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    deck_id = Column(String(36), ForeignKey("flashcard_decks.id", ondelete="SET NULL"), nullable=True)
    duration_minutes = Column(Integer, nullable=False, default=25)
    elapsed_seconds = Column(Integer, nullable=False, default=0)
    cards_reviewed = Column(Integer, nullable=False, default=0)
    status = Column(String(30), nullable=False, default="IN_PROGRESS")  # 'IN_PROGRESS', 'COMPLETED', 'ABORTED'
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", foreign_keys=[user_id])
    deck = relationship("FlashcardDeck", foreign_keys=[deck_id])
