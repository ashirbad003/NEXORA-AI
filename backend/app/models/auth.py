import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, Table, Text, Integer, Float, Index
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from backend.app.db.session import Base

# Association Table for Many-to-Many User <-> Role
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("assigned_at", DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)),
    Index("ix_user_roles_user_id", "user_id"),
    Index("ix_user_roles_role_id", "role_id")
)

class Role(Base):
    __tablename__ = "roles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)

    users = relationship("User", secondary=user_roles, back_populates="roles")

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    phone_number = Column(String(30), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    
    is_active = Column(Boolean, default=True, nullable=False)
    is_email_verified = Column(Boolean, default=False, nullable=False)
    is_phone_verified = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    roles = relationship("Role", secondary=user_roles, back_populates="users", lazy="selectin")
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="selectin")
    admin_profile = relationship("AdminProfile", back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="selectin")
    placement_profile = relationship("PlacementCellProfile", back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="selectin")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")

class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    institution = Column(String(255), nullable=True)
    department = Column(String(100), nullable=True, index=True)
    batch_year = Column(Integer, nullable=True, index=True)
    cgpa = Column(Float, nullable=True)
    skills = Column(Text, nullable=True)  # Comma-separated or JSON string
    career_preferences = Column(Text, nullable=True)
    readiness_score = Column(Integer, default=0, nullable=False)
    timezone = Column(String(64), default="UTC", nullable=False)

    user = relationship("User", back_populates="student_profile")

class AdminProfile(Base):
    __tablename__ = "admin_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    admin_level = Column(String(50), default="STANDARD", nullable=False)
    department_access = Column(String(255), default="ALL", nullable=False)

    user = relationship("User", back_populates="admin_profile")

class PlacementCellProfile(Base):
    __tablename__ = "placement_cell_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    institution = Column(String(255), nullable=False)
    department = Column(String(100), nullable=True)
    designation = Column(String(100), default="Placement Officer", nullable=False)

    user = relationship("User", back_populates="placement_profile")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="refresh_tokens")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(255), nullable=True)
    ip_address = Column(String(50), nullable=True)
    details = Column(Text, nullable=True)  # JSON formatted non-secret metadata
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    user = relationship("User", back_populates="audit_logs")
