from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# ==========================================
# MODULE J: RESUME INTELLIGENCE (FEAT-181 to FEAT-200)
# ==========================================

class ResumeCreateRequest(BaseModel):
    title: str = Field(default="My Technical Resume", max_length=100)
    template_type: str = Field(default="Modern", description="Modern, LaTeX, Minimal, FAANG")
    raw_content: Optional[str] = None
    structured_data: Dict[str, Any] = Field(default_factory=dict)
    is_primary: bool = True

class ResumeUpdateRequest(BaseModel):
    title: Optional[str] = None
    template_type: Optional[str] = None
    raw_content: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    is_primary: Optional[bool] = None

class ResumeResponse(BaseModel):
    id: str
    student_id: str
    title: str
    template_type: str
    raw_content: Optional[str] = None
    structured_data: Dict[str, Any]
    ats_score: float
    completeness_score: float
    is_primary: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ATSAnalysisResponse(BaseModel):
    resume_id: str
    ats_score: float
    completeness_score: float
    keyword_matches: List[str]
    missing_critical_keywords: List[str]
    formatting_issues: List[str]
    action_verb_suggestions: List[str]
    quantitative_metric_feedback: str
    summary_verdict: str

class BulletOptimizationRequest(BaseModel):
    bullet_point: str
    role_target: Optional[str] = "Software Engineer"

class BulletOptimizationResponse(BaseModel):
    original: str
    optimized: str
    action_verb_used: str
    metric_added: bool
    explanation: str

# ==========================================
# MODULE K: GITHUB PORTFOLIO INTELLIGENCE (FEAT-201 to FEAT-216)
# ==========================================

class GitHubScanRequest(BaseModel):
    github_username: str = Field(..., min_length=1, max_length=100)

class RepositoryHealth(BaseModel):
    name: str
    description: Optional[str] = None
    primary_language: Optional[str] = None
    has_readme: bool
    has_license: bool
    stars_count: int = 0
    forks_count: int = 0
    open_issues_count: int = 0
    health_score: float  # 0 - 100
    recommendations: List[str] = []

class GitHubProfileResponse(BaseModel):
    id: str
    student_id: str
    github_username: str
    portfolio_score: float
    public_repos_count: int
    languages_distribution: Dict[str, float]  # Percentage by language
    repository_health_metrics: List[RepositoryHealth]
    recommendations: List[str]
    last_scanned_at: datetime

    class Config:
        from_attributes = True

# ==========================================
# MODULE L: JOBS & INTERNSHIPS INTELLIGENCE (FEAT-217 to FEAT-234)
# ==========================================

class JobOpportunityCreateRequest(BaseModel):
    company_name: str
    role_title: str
    opportunity_type: str = "Full-Time"  # Full-Time, Internship
    location: str = "Remote"
    stipend_or_salary: str = "Competitive"
    description: str
    required_skills: List[str] = []
    deadline: Optional[datetime] = None
    is_on_campus: bool = False
    application_url: str = "#"

class JobOpportunityResponse(BaseModel):
    id: str
    company_name: str
    role_title: str
    opportunity_type: str
    location: str
    stipend_or_salary: str
    description: str
    required_skills: List[str]
    deadline: Optional[datetime] = None
    is_on_campus: bool
    application_url: str
    created_at: datetime
    match_score: Optional[float] = None  # Calculated dynamically for student

    class Config:
        from_attributes = True

class ApplicationStatusUpdateRequest(BaseModel):
    status: str = Field(..., description="Wishlist, Applied, Interview, Offer, Rejected")
    interview_date: Optional[datetime] = None
    notes: Optional[str] = None

class JobApplicationResponse(BaseModel):
    id: str
    job_id: str
    student_id: str
    status: str
    match_score: float
    applied_at: Optional[datetime] = None
    interview_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ColdEmailDraftRequest(BaseModel):
    job_id: str
    hiring_manager_name: Optional[str] = "Hiring Team"
    key_highlights: Optional[List[str]] = None

class ColdEmailDraftResponse(BaseModel):
    subject_line: str
    body_text: str
    tips: List[str]
