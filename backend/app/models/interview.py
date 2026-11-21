import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.auth import Base

class MockInterviewSession(Base):
    __tablename__ = "mock_interview_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_target: Mapped[str] = mapped_column(String(100), default="Software Development Engineer", nullable=False)
    interview_type: Mapped[str] = mapped_column(String(50), default="Technical", nullable=False)  # Technical, HR & Behavioral, System Design
    company_persona: Mapped[str] = mapped_column(String(50), default="Google", nullable=False)  # FEAT-109 (Google, Amazon, TCS, etc.)
    status: Mapped[str] = mapped_column(String(20), default="in_progress", nullable=False)  # in_progress, completed
    total_turns: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 0-100 Readiness Scorecard (FEAT-117)
    star_situation_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # FEAT-111
    star_task_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    star_action_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    star_result_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tone_clarity_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # FEAT-112
    filler_word_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    technical_accuracy_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # FEAT-113
    improvement_plan: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # FEAT-116
    whiteboard_state: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # FEAT-120
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    turns: Mapped[List["MockInterviewTurn"]] = relationship("MockInterviewTurn", back_populates="session", cascade="all, delete-orphan")

class MockInterviewTurn(Base):
    __tablename__ = "mock_interview_turns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("mock_interview_sessions.id", ondelete="CASCADE"), nullable=False)
    turn_index: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_category: Mapped[str] = mapped_column(String(50), default="Technical", nullable=False)
    student_response_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    audio_duration_seconds: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # FEAT-118
    pacing_verdict: Mapped[str] = mapped_column(String(50), default="Optimal", nullable=False)  # Optimal, Too Brief, Rambling
    interviewer_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_followup: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # FEAT-110
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    session: Mapped["MockInterviewSession"] = relationship("MockInterviewSession", back_populates="turns")
