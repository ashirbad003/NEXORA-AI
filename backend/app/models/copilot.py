from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from backend.app.models.auth import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class CopilotCareerPath(Base):
    """
    Stores student's chosen career track, target companies, and preferences (FEAT-021, FEAT-024).
    """
    __tablename__ = "copilot_career_paths"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    target_role = Column(String(100), nullable=False, default="Software Development Engineer")
    target_companies = Column(JSON, default=list) # e.g. ["Google", "Amazon", "Microsoft"]
    target_salary_min_lpa = Column(Float, default=12.0)
    target_salary_max_lpa = Column(Float, default=25.0)
    preferred_persona = Column(String(50), default="friendly_mentor") # friendly_mentor, strict_interviewer, technical_architect
    preferred_language = Column(String(20), default="en") # en, hi, hinglish
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CopilotRoadmap(Base):
    """
    Stores generated 90-day placement roadmap and weekly milestones (FEAT-022, FEAT-031, FEAT-033).
    """
    __tablename__ = "copilot_roadmaps"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    target_role = Column(String(100), nullable=False)
    duration_weeks = Column(Integer, default=12)
    weeks_data = Column(JSON, default=list) # list of week milestone objects
    current_week = Column(Integer, default=1)
    milestone_badges = Column(JSON, default=list) # e.g. ["Bronze Starter", "Silver Algorithmist"]
    is_active = Column(Boolean, default=True)
    readiness_index_target = Column(Float, default=85.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CopilotSprintTask(Base):
    """
    Stores daily sprints and actionable task items (FEAT-023, FEAT-028).
    """
    __tablename__ = "copilot_sprint_tasks"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    roadmap_id = Column(String(36), ForeignKey("copilot_roadmaps.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(50), default="coding") # coding, learning, quiz, revision, project
    estimated_minutes = Column(Integer, default=30)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    date_assigned = Column(String(10), nullable=False) # YYYY-MM-DD
    created_at = Column(DateTime, default=datetime.utcnow)

class CopilotConversation(Base):
    """
    Stores multi-turn AI mentorship chat sessions (FEAT-010, FEAT-032).
    """
    __tablename__ = "copilot_conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_title = Column(String(255), default="Career Mentorship Session")
    persona = Column(String(50), default="friendly_mentor")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CopilotMessage(Base):
    """
    Stores individual conversation turn and token usage (FEAT-004, FEAT-010, FEAT-015).
    """
    __tablename__ = "copilot_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("copilot_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False) # user, assistant, system
    content = Column(Text, nullable=False)
    tokens_prompt = Column(Integer, default=0)
    tokens_completion = Column(Integer, default=0)
    confidence_score = Column(Float, default=1.0)
    feedback_rating = Column(Integer, nullable=True) # 1 (up), -1 (down), null
    created_at = Column(DateTime, default=datetime.utcnow)
