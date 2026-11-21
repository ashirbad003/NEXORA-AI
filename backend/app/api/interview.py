from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db_session
from backend.app.api.deps import get_current_user
from backend.app.models.auth import User
from backend.app.schemas.interview import (
    MockInterviewStartSchema, MockInterviewSessionResponseSchema,
    MockInterviewRespondSchema, MockInterviewEvaluationSchema
)
from backend.app.services.interview_service import InterviewService

router = APIRouter(prefix="/interview", tags=["Mock Interview"])

@router.post("/start", response_model=MockInterviewSessionResponseSchema)
async def start_mock_interview(
    data: MockInterviewStartSchema,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Start interactive AI Mock Interview session (FEAT-103, FEAT-107, FEAT-108, FEAT-109)"""
    return await InterviewService.start_session(db, student_id=current_user.id, data=data)

@router.post("/sessions/{session_id}/respond")
async def respond_to_interviewer(
    session_id: str,
    data: MockInterviewRespondSchema,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Submit student verbal/text response and receive dynamic follow-up (FEAT-104, FEAT-106, FEAT-110, FEAT-118, FEAT-120)"""
    return await InterviewService.process_response(
        db, session_id=session_id, student_id=current_user.id, data=data
    )

@router.get("/sessions/{session_id}/evaluation", response_model=MockInterviewEvaluationSchema)
async def get_interview_evaluation(
    session_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """Retrieve STAR rubric evaluation and readiness scorecard (FEAT-111, FEAT-112, FEAT-113, FEAT-115, FEAT-116, FEAT-117)"""
    return await InterviewService.evaluate_and_conclude_session(
        db, session_id=session_id, student_id=current_user.id
    )
