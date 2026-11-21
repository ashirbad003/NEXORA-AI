import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.models.auth import Base

# ==========================================
# MODULE M: PLACEMENT CELL PORTAL (FEAT-235 to FEAT-256)
# ==========================================

class PlacementDrive(Base):
    __tablename__ = "placement_drives"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_name: Mapped[str] = mapped_column(String(150), nullable=False)
    role_title: Mapped[str] = mapped_column(String(150), nullable=False)
    ctc_lpa: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # in Lakhs per annum
    tier: Mapped[str] = mapped_column(String(50), default="Standard", nullable=False)  # Standard, Dream, Super-Dream (FEAT-255)
    status: Mapped[str] = mapped_column(String(50), default="Scheduled", nullable=False)  # Draft, Scheduled, Registration Open, Ongoing, Completed, Cancelled (FEAT-239)
    min_cgpa: Mapped[float] = mapped_column(Float, default=6.0, nullable=False)  # FEAT-237
    allowed_branches: Mapped[list] = mapped_column(JSON, default=list, nullable=False)  # ["CSE", "ECE", "IT"]
    max_backlogs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    registration_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    drive_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    registrations: Mapped[List["PlacementDriveRegistration"]] = relationship("PlacementDriveRegistration", back_populates="drive", cascade="all, delete-orphan")
    offers: Mapped[List["PlacementOffer"]] = relationship("PlacementOffer", back_populates="drive", cascade="all, delete-orphan")

class PlacementDriveRegistration(Base):
    __tablename__ = "placement_drive_registrations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    drive_id: Mapped[str] = mapped_column(String(36), ForeignKey("placement_drives.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Pending", nullable=False)  # Pending, Approved, Rejected, Shortlisted, Selected (FEAT-240, FEAT-241)
    is_eligible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    attendance: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    interview_slot: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # FEAT-250
    tpo_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    drive: Mapped["PlacementDrive"] = relationship("PlacementDrive", back_populates="registrations")

class PlacementOffer(Base):
    __tablename__ = "placement_offers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    drive_id: Mapped[str] = mapped_column(String(36), ForeignKey("placement_drives.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    company_name: Mapped[str] = mapped_column(String(150), nullable=False)
    designation: Mapped[str] = mapped_column(String(150), nullable=False)
    ctc_lpa: Mapped[float] = mapped_column(Float, nullable=False)
    offer_letter_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # FEAT-242
    status: Mapped[str] = mapped_column(String(50), default="Offered", nullable=False)  # Offered, Accepted, Declined
    offered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    drive: Mapped["PlacementDrive"] = relationship("PlacementDrive", back_populates="offers")

class StudentPlacementProfile(Base):
    __tablename__ = "student_placement_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    is_blacklisted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # FEAT-251
    blacklist_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_opted_out: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # FEAT-248 (Higher studies, etc)
    opt_out_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    offers_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    highest_offer_lpa: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

# ==========================================
# MODULE N: ADMIN INTELLIGENCE PORTAL (FEAT-257 to FEAT-276)
# ==========================================

class SystemFeatureFlag(Base):
    __tablename__ = "system_feature_flags"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    flag_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)  # FEAT-262
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    updated_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class SystemMetricSnapshot(Base):
    __tablename__ = "system_metric_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False)  # HEALTH, COST_TELEMETRY, SANDBOX_QUEUE (FEAT-270, FEAT-272, FEAT-273)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
