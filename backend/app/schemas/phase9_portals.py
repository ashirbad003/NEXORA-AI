from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# ==========================================
# MODULE M: PLACEMENT CELL SCHEMAS (FEAT-235 to FEAT-256)
# ==========================================

class PlacementDriveCreateRequest(BaseModel):
    company_name: str
    role_title: str
    ctc_lpa: float = Field(..., ge=0.0)
    tier: str = Field(default="Standard", description="Standard, Dream, Super-Dream")
    min_cgpa: float = Field(default=6.0, ge=0.0, le=10.0)
    allowed_branches: List[str] = Field(default=["CSE", "IT", "ECE"])
    max_backlogs: int = Field(default=0, ge=0)
    registration_deadline: Optional[datetime] = None
    drive_date: Optional[datetime] = None
    description: str

class PlacementDriveResponse(BaseModel):
    id: str
    company_name: str
    role_title: str
    ctc_lpa: float
    tier: str
    status: str
    min_cgpa: float
    allowed_branches: List[str]
    max_backlogs: int
    registration_deadline: Optional[datetime] = None
    drive_date: Optional[datetime] = None
    description: str
    created_at: datetime

    class Config:
        from_attributes = True

class DriveRegisterRequest(BaseModel):
    drive_id: str

class DriveRegistrationResponse(BaseModel):
    id: str
    drive_id: str
    student_id: str
    status: str
    is_eligible: bool
    attendance: bool
    interview_slot: Optional[str] = None
    tpo_notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class RegistrationStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="Pending, Approved, Rejected, Shortlisted, Selected")
    interview_slot: Optional[str] = None
    attendance: Optional[bool] = None
    tpo_notes: Optional[str] = None

class OfferCreateRequest(BaseModel):
    drive_id: str
    student_id: str
    company_name: str
    designation: str
    ctc_lpa: float
    offer_letter_url: Optional[str] = None

class OfferResponse(BaseModel):
    id: str
    drive_id: str
    student_id: str
    company_name: str
    designation: str
    ctc_lpa: float
    offer_letter_url: Optional[str] = None
    status: str
    offered_at: datetime

    class Config:
        from_attributes = True

class StudentPlacementProfileResponse(BaseModel):
    id: str
    student_id: str
    is_blacklisted: bool
    blacklist_reason: Optional[str] = None
    is_opted_out: bool
    opt_out_reason: Optional[str] = None
    offers_count: int
    highest_offer_lpa: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BlacklistUpdateRequest(BaseModel):
    is_blacklisted: bool
    reason: Optional[str] = None

class OptOutUpdateRequest(BaseModel):
    is_opted_out: bool
    reason: Optional[str] = None

class InstitutionalDashboardStats(BaseModel):
    total_eligible_students: int
    total_drives: int
    total_offers_extended: int
    placed_students_count: int
    placement_percentage: float
    average_ctc_lpa: float
    highest_ctc_lpa: float
    branch_wise_stats: Dict[str, Any]

# ==========================================
# MODULE N: ADMIN INTELLIGENCE SCHEMAS (FEAT-257 to FEAT-276)
# ==========================================

class FeatureFlagUpdateRequest(BaseModel):
    flag_key: str
    is_enabled: bool
    name: Optional[str] = None
    description: Optional[str] = None

class FeatureFlagResponse(BaseModel):
    id: str
    flag_key: str
    name: str
    description: Optional[str] = None
    is_enabled: bool
    updated_by: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True

class SystemHealthTelemetry(BaseModel):
    status: str
    database_connected: bool
    active_connections: int
    docker_sandbox_status: str
    sandbox_queue_pending: int
    ai_provider: str
    total_tokens_consumed_24h: int
    avg_api_latency_ms: float
    error_rate_5xx_pct: float
    timestamp: datetime

class DiagnosticReportResponse(BaseModel):
    report_id: str
    generated_at: datetime
    system_version: str
    healthy: bool
    checks: Dict[str, Any]
    active_flags: List[str]
    telemetry_summary: Dict[str, Any]
