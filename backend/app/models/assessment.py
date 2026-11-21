import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.auth import Base

class AssessmentTest(Base):
    __tablename__ = "assessment_tests"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), default="Aptitude", nullable=False)  # Aptitude, Technical, Core CS, Mock Drive
    difficulty: Mapped[str] = mapped_column(String(20), default="Medium", nullable=False)  # Easy, Medium, Hard, Adaptive
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    total_marks: Mapped[float] = mapped_column(Float, default=30.0, nullable=False)
    pass_marks: Mapped[float] = mapped_column(Float, default=15.0, nullable=False)
    negative_marking_rate: Mapped[float] = mapped_column(Float, default=0.25, nullable=False)  # FEAT-045
    retake_allowed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # FEAT-060
    retake_cooldown_hours: Mapped[int] = mapped_column(Integer, default=24, nullable=False)
    company_template: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # FEAT-051 (e.g. TCS NQT, Amazon, Infosys)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    questions: Mapped[List["AssessmentQuestion"]] = relationship("AssessmentQuestion", back_populates="test", cascade="all, delete-orphan")
    attempts: Mapped[List["AssessmentAttempt"]] = relationship("AssessmentAttempt", back_populates="test", cascade="all, delete-orphan")

class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    test_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessment_tests.id", ondelete="CASCADE"), nullable=False)
    section_name: Mapped[str] = mapped_column(String(50), default="General", nullable=False)  # FEAT-047 (e.g. Aptitude, Technical, Core CS)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[dict] = mapped_column(JSON, nullable=False)  # e.g. {"A": "...", "B": "...", "C": "...", "D": "..."}
    correct_option: Mapped[str] = mapped_column(String(10), nullable=False)  # e.g. "A"
    marks: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # FEAT-049
    topic_tag: Mapped[str] = mapped_column(String(100), default="General", nullable=False)  # FEAT-055
    difficulty: Mapped[str] = mapped_column(String(20), default="Medium", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    test: Mapped["AssessmentTest"] = relationship("AssessmentTest", back_populates="questions")
    answers: Mapped[List["AssessmentAnswer"]] = relationship("AssessmentAnswer", back_populates="question", cascade="all, delete-orphan")

class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    test_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessment_tests.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="in_progress", nullable=False)  # in_progress, completed, expired
    start_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    accuracy_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    percentile: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    blur_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # FEAT-053
    shuffled_question_order: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # FEAT-044
    flagged_question_ids: Mapped[Optional[list]] = mapped_column(JSON, default=list, nullable=True)  # FEAT-046
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    test: Mapped["AssessmentTest"] = relationship("AssessmentTest", back_populates="attempts")
    answers: Mapped[List["AssessmentAnswer"]] = relationship("AssessmentAnswer", back_populates="attempt", cascade="all, delete-orphan")

class AssessmentAnswer(Base):
    __tablename__ = "assessment_answers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    attempt_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[str] = mapped_column(String(36), ForeignKey("assessment_questions.id", ondelete="CASCADE"), nullable=False)
    selected_option: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    is_correct: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    marks_awarded: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_saved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    attempt: Mapped["AssessmentAttempt"] = relationship("AssessmentAttempt", back_populates="answers")
    question: Mapped["AssessmentQuestion"] = relationship("AssessmentQuestion", back_populates="answers")
