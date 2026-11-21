from typing import List
from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db_session
from backend.app.api.deps import get_current_user, require_roles
from backend.app.models.auth import User
from backend.app.schemas.user import UserRoleEnum
from backend.app.schemas.phase8_intelligence import (
    ResumeCreateRequest, ResumeUpdateRequest, ResumeResponse,
    ATSAnalysisResponse, BulletOptimizationRequest, BulletOptimizationResponse
)
from backend.app.services.resume_service import ResumeIntelligenceService

router = APIRouter(prefix="/resume", tags=["Resume Intelligence (Phase 8)"])

@router.post("/", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def create_resume(
    payload: ResumeCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    return await ResumeIntelligenceService.create_resume(session, current_user.id, payload)

@router.get("/", response_model=List[ResumeResponse])
async def list_resumes(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    return await ResumeIntelligenceService.get_resumes_for_student(session, current_user.id)

@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    return await ResumeIntelligenceService.get_resume_by_id(session, resume_id, current_user.id)

@router.put("/{resume_id}", response_model=ResumeResponse)
async def update_resume(
    resume_id: str,
    payload: ResumeUpdateRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    return await ResumeIntelligenceService.update_resume(session, resume_id, current_user.id, payload)

@router.get("/{resume_id}/ats-analysis", response_model=ATSAnalysisResponse)
async def analyze_ats(
    resume_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    return await ResumeIntelligenceService.analyze_resume_ats(session, resume_id, current_user.id)

@router.post("/optimize-bullet", response_model=BulletOptimizationResponse)
async def optimize_bullet(
    payload: BulletOptimizationRequest,
    current_user: User = Depends(get_current_user)
):
    return ResumeIntelligenceService.optimize_bullet_point(payload.bullet_point, payload.role_target or "Software Engineer")

@router.get("/{resume_id}/export/latex")
async def export_latex(
    resume_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    resume = await ResumeIntelligenceService.get_resume_by_id(session, resume_id, current_user.id)
    latex_code = ResumeIntelligenceService.generate_latex_resume(resume)
    return Response(content=latex_code, media_type="text/plain")
