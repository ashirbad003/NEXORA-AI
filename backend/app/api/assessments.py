from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db_session
from backend.app.api.deps import get_current_user
from backend.app.models.auth import User
from backend.app.schemas.assessment import (
    AssessmentTestCreateSchema, AssessmentTestResponseSchema,
    AttemptStartResponseSchema, AnswerBatchSaveSchema, ScorecardResponseSchema
)
from backend.app.services.assessment_service import AssessmentService

router = APIRouter(prefix="/assessments", tags=["Assessments"])

@router.get("/tests", response_model=List[AssessmentTestResponseSchema])
async def list_assessments(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """List all published assessment tests (FEAT-041, FEAT-051, FEAT-052)"""
    return await AssessmentService.list_published_tests(db)

@router.post("/tests", response_model=Dict[str, Any])
async def create_assessment(
    data: AssessmentTestCreateSchema,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Admin question bank and test creation (FEAT-058, FEAT-059)"""
    test = await AssessmentService.create_test(db, data)
    return {"status": "created", "test_id": test.id, "title": test.title}

@router.post("/tests/{test_id}/start", response_model=AttemptStartResponseSchema)
async def start_or_resume_test(
    test_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Start or resume assessment with server-authoritative timer and shuffled questions (FEAT-041, FEAT-043, FEAT-044)"""
    return await AssessmentService.start_or_resume_attempt(db, test_id=test_id, student_id=current_user.id)

@router.put("/attempts/{attempt_id}/save")
async def save_answers(
    attempt_id: str,
    data: AnswerBatchSaveSchema,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Auto-save answer state, flags, and window blur events (FEAT-042, FEAT-046, FEAT-053)"""
    return await AssessmentService.save_answers_batch(
        db, attempt_id=attempt_id, student_id=current_user.id, data=data
    )

@router.post("/attempts/{attempt_id}/submit", response_model=ScorecardResponseSchema)
async def submit_test_attempt(
    attempt_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Submit attempt and generate diagnostic scorecard (FEAT-045, FEAT-048, FEAT-049, FEAT-055)"""
    return await AssessmentService.submit_attempt(db, attempt_id=attempt_id, student_id=current_user.id)

@router.get("/attempts/{attempt_id}/scorecard", response_model=ScorecardResponseSchema)
async def get_scorecard(
    attempt_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Retrieve comprehensive diagnostic scorecard (FEAT-048)"""
    return await AssessmentService.get_scorecard(db, attempt_id=attempt_id, student_id=current_user.id)

@router.get("/history", response_model=List[Dict[str, Any]])
async def get_student_assessment_history(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Retrieve historical assessment trends (FEAT-054)"""
    return await AssessmentService.get_historical_trends(db, student_id=current_user.id)

@router.get("/leaderboard/{test_id}", response_model=List[Dict[str, Any]])
async def get_test_leaderboard(
    test_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Leaderboard for public assessments (FEAT-056)"""
    return await AssessmentService.get_public_leaderboard(db, test_id=test_id)
