import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, Table, Text, Integer, Float, Index
)
from sqlalchemy.orm import relationship
from backend.app.db.session import Base

class CodingProblem(Base):
    """
    Coding Problem bank entity (FEAT-065, FEAT-066, FEAT-079, FEAT-080).
    Categorized by difficulty, tags, and company interview appearances.
    """
    __tablename__ = "coding_problems"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    slug = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    difficulty = Column(String(20), nullable=False, index=True)  # Easy, Medium, Hard
    category = Column(String(50), nullable=False, index=True)    # Arrays, DP, Graphs, etc.
    tags = Column(String(255), nullable=True)                    # Comma-separated: Two Pointers, Hash Table
    companies = Column(String(255), nullable=True)               # Comma-separated: Google, Amazon, Microsoft
    description_markdown = Column(Text, nullable=False)
    constraints = Column(Text, nullable=True)
    time_limit_ms = Column(Integer, default=2000, nullable=False)
    memory_limit_mb = Column(Integer, default=128, nullable=False)
    starter_code_python = Column(Text, nullable=True)
    starter_code_java = Column(Text, nullable=True)
    starter_code_cpp = Column(Text, nullable=True)
    starter_code_c = Column(Text, nullable=True)
    is_published = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    test_cases = relationship("ProblemTestCase", back_populates="problem", cascade="all, delete-orphan")
    submissions = relationship("CodeSubmission", back_populates="problem", cascade="all, delete-orphan")

class ProblemTestCase(Base):
    """
    Sample and Hidden test cases for code evaluation (FEAT-067, FEAT-068).
    Strictly shields hidden test outputs from student inspection.
    """
    __tablename__ = "problem_test_cases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    problem_id = Column(String(36), ForeignKey("coding_problems.id", ondelete="CASCADE"), nullable=False, index=True)
    stdin_input = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=False)
    is_sample = Column(Boolean, default=False, nullable=False)  # True = sample visible to user; False = hidden
    explanation = Column(Text, nullable=True)
    order_index = Column(Integer, default=0, nullable=False)

    problem = relationship("CodingProblem", back_populates="test_cases")

class CodeSubmission(Base):
    """
    Student solution submission record (FEAT-073).
    Tracks verdict, runtime, memory, and code content. Strictly user-isolated.
    """
    __tablename__ = "code_submissions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    problem_id = Column(String(36), ForeignKey("coding_problems.id", ondelete="CASCADE"), nullable=False, index=True)
    language = Column(String(20), nullable=False)               # python, java, cpp, c
    code_content = Column(Text, nullable=False)
    verdict = Column(String(30), nullable=False, index=True)    # ACCEPTED, WRONG_ANSWER, TIME_LIMIT_EXCEEDED, etc.
    passed_test_cases = Column(Integer, default=0, nullable=False)
    total_test_cases = Column(Integer, default=0, nullable=False)
    execution_time_ms = Column(Float, default=0.0, nullable=False)
    memory_used_mb = Column(Float, default=0.0, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    problem = relationship("CodingProblem", back_populates="submissions")

    __table_args__ = (
        Index("ix_code_submissions_user_problem", "user_id", "problem_id"),
    )

class StudentCodingStats(Base):
    """
    Student coding streak and problem-solving aggregated profile (FEAT-074).
    """
    __tablename__ = "student_coding_stats"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    total_solved = Column(Integer, default=0, nullable=False)
    easy_solved = Column(Integer, default=0, nullable=False)
    medium_solved = Column(Integer, default=0, nullable=False)
    hard_solved = Column(Integer, default=0, nullable=False)
    current_streak_days = Column(Integer, default=0, nullable=False)
    longest_streak_days = Column(Integer, default=0, nullable=False)
    last_solved_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
