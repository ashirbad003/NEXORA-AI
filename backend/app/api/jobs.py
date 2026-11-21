from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db_session
from backend.app.api.deps import get_current_user, require_roles
from backend.app.models.auth import User
from backend.app.schemas.user import UserRoleEnum
from backend.app.schemas.phase8_intelligence import (
    JobOpportunityCreateRequest, JobOpportunityResponse,
    ApplicationStatusUpdateRequest, JobApplicationResponse,
    ColdEmailDraftRequest, ColdEmailDraftResponse
)
from backend.app.services.job_service import JobIntelligenceService

router = APIRouter(prefix="/jobs", tags=["Jobs & Opportunities Intelligence (Phase 8)"])

@router.get("/opportunities", response_model=List[JobOpportunityResponse])
async def list_job_opportunities(
    role: Optional[str] = Query(None, description="Search role title or company"),
    opportunity_type: Optional[str] = Query(None, description="Full-Time or Internship"),
    on_campus: bool = Query(False, description="Filter for on-campus drives"),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    return await JobIntelligenceService.list_jobs(
        session,
        student_id=current_user.id,
        role_filter=role,
        type_filter=opportunity_type,
        on_campus_only=on_campus
    )

@router.post("/opportunities", response_model=JobOpportunityResponse, status_code=status.HTTP_201_CREATED)
async def create_job_opportunity(
    payload: JobOpportunityCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    admin_user: User = Depends(require_roles([UserRoleEnum.ADMIN, UserRoleEnum.PLACEMENT_CELL]))
):
    job = await JobIntelligenceService.create_job(session, payload)
    return JobOpportunityResponse(
        id=job.id,
        company_name=job.company_name,
        role_title=job.role_title,
        opportunity_type=job.opportunity_type,
        location=job.location,
        stipend_or_salary=job.stipend_or_salary,
        description=job.description,
        required_skills=job.required_skills,
        deadline=job.deadline,
        is_on_campus=job.is_on_campus,
        application_url=job.application_url,
        created_at=job.created_at,
        match_score=85.0
    )

@router.get("/applications", response_model=List[JobApplicationResponse])
async def list_my_applications(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    return await JobIntelligenceService.get_student_applications(session, current_user.id)

@router.post("/applications/{job_id}", response_model=JobApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply_for_job(
    job_id: str,
    status_state: str = Query("Applied", description="Wishlist or Applied"),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    return await JobIntelligenceService.apply_or_save_job(
        session, current_user.id, job_id, initial_status=status_state
    )

@router.patch("/applications/{application_id}/status", response_model=JobApplicationResponse)
async def update_application_status(
    application_id: str,
    payload: ApplicationStatusUpdateRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    return await JobIntelligenceService.update_application_status(
        session, application_id, current_user.id, payload
    )

@router.post("/cold-email", response_model=ColdEmailDraftResponse)
async def draft_cold_email(
    payload: ColdEmailDraftRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    return await JobIntelligenceService.generate_cold_email(session, current_user.id, payload)
