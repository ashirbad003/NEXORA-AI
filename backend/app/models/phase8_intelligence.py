import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.auth import Base

class ResumeDocument(Base):
    __tablename__ = "resume_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(100), default="My Technical Resume", nullable=False)
    template_type: Mapped[str] = mapped_column(String(50), default="Modern", nullable=False)  # Modern, LaTeX, Minimal, FAANG (FEAT-186, FEAT-199)
    raw_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    structured_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)  # contact, education, skills, experience, projects
    ats_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 0-100 (FEAT-182)
    completeness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # FEAT-197
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class GitHubProfileCache(Base):
    __tablename__ = "github_profile_caches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    github_username: Mapped[str] = mapped_column(String(100), nullable=False)
    portfolio_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 0-100 (FEAT-212)
    public_repos_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    languages_distribution: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)  # FEAT-203
    repository_health_metrics: Mapped[list] = mapped_column(JSON, default=list, nullable=False)  # FEAT-202
    recommendations: Mapped[list] = mapped_column(JSON, default=list, nullable=False)  # FEAT-213
    last_scanned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

class JobOpportunity(Base):
    __tablename__ = "job_opportunities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_name: Mapped[str] = mapped_column(String(150), nullable=False)
    role_title: Mapped[str] = mapped_column(String(150), nullable=False)
    opportunity_type: Mapped[str] = mapped_column(String(50), default="Full-Time", nullable=False)  # Full-Time, Internship (FEAT-217, FEAT-223)
    location: Mapped[str] = mapped_column(String(100), default="Remote", nullable=False)
    stipend_or_salary: Mapped[str] = mapped_column(String(100), default="Competitive", nullable=False)  # FEAT-227
    description: Mapped[str] = mapped_column(Text, nullable=False)
    required_skills: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # FEAT-220
    is_on_campus: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # FEAT-223
    application_url: Mapped[str] = mapped_column(String(255), default="#", nullable=False)  # FEAT-233
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    applications: Mapped[List["JobApplication"]] = relationship("JobApplication", back_populates="job", cascade="all, delete-orphan")

class JobApplication(Base):
    __tablename__ = "job_applications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("job_opportunities.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Wishlist", nullable=False)  # Wishlist, Applied, Interview, Offer, Rejected (FEAT-219 Kanban)
    match_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 0-100 (FEAT-218)
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    interview_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # FEAT-225
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # FEAT-226 Lessons learned
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    job: Mapped["JobOpportunity"] = relationship("JobOpportunity", back_populates="applications")
