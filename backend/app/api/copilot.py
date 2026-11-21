from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List

from backend.app.db.session import get_db_session
from backend.app.api.deps import get_current_user
from backend.app.models.auth import User
from backend.app.schemas.copilot import (
    CareerPathSelectRequest, CareerPathResponse, RoadmapGenerateRequest,
    SprintTaskToggleRequest, CopilotChatRequest, FeedbackRequest, TriviaAnswerRequest
)
from backend.app.services.copilot_service import CopilotService

router = APIRouter(prefix="/copilot", tags=["AI Career Copilot"])

@router.get("/career-path", response_model=CareerPathResponse)
async def get_career_path(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Get current student career track preferences (FEAT-021)."""
    cp = await CopilotService.get_or_create_career_path(db, current_user.id)
    return CareerPathResponse(
        target_role=cp.target_role,
        target_companies=cp.target_companies or [],
        target_salary_min_lpa=cp.target_salary_min_lpa or 12.0,
        target_salary_max_lpa=cp.target_salary_max_lpa or 25.0,
        preferred_persona=cp.preferred_persona or "friendly_mentor",
        preferred_language=cp.preferred_language or "en",
        updated_at=cp.updated_at
    )

@router.post("/career-path", response_model=CareerPathResponse)
async def update_career_path(
    req: CareerPathSelectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Update student career track preferences (FEAT-021, FEAT-024)."""
    cp = await CopilotService.update_career_path(
        db,
        current_user.id,
        target_role=req.target_role,
        target_companies=req.target_companies,
        salary_min=req.target_salary_min_lpa,
        salary_max=req.target_salary_max_lpa,
        persona=req.preferred_persona,
        language=req.preferred_language
    )
    return CareerPathResponse(
        target_role=cp.target_role,
        target_companies=cp.target_companies or [],
        target_salary_min_lpa=cp.target_salary_min_lpa,
        target_salary_max_lpa=cp.target_salary_max_lpa,
        preferred_persona=cp.preferred_persona,
        preferred_language=cp.preferred_language,
        updated_at=cp.updated_at
    )

@router.get("/roadmap")
async def get_roadmap(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve 90-day placement roadmap (FEAT-022, FEAT-031)."""
    rm = await CopilotService.get_or_generate_roadmap(db, current_user.id)
    return {
        "id": rm.id,
        "target_role": rm.target_role,
        "duration_weeks": rm.duration_weeks,
        "weeks": rm.weeks_data,
        "current_week": rm.current_week,
        "milestone_badges": rm.milestone_badges,
        "readiness_index_target": rm.readiness_index_target
    }

@router.post("/roadmap/generate")
async def generate_roadmap(
    req: RoadmapGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Generate or re-generate placement roadmap (FEAT-022, FEAT-033)."""
    rm = await CopilotService.get_or_generate_roadmap(db, current_user.id, force_regenerate=req.force_regenerate)
    return {
        "id": rm.id,
        "target_role": rm.target_role,
        "duration_weeks": rm.duration_weeks,
        "weeks": rm.weeks_data,
        "milestone_badges": rm.milestone_badges,
        "status": "generated"
    }

@router.get("/sprints/today")
async def get_today_sprints(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Fetch daily action sprint tasks (FEAT-023, FEAT-028)."""
    tasks = await CopilotService.get_daily_sprints(db, current_user.id)
    return [
        {
            "id": t.id,
            "title": t.title,
            "category": t.category,
            "estimated_minutes": t.estimated_minutes,
            "is_completed": t.is_completed,
            "date_assigned": t.date_assigned
        }
        for t in tasks
    ]

@router.patch("/sprints/{task_id}")
async def toggle_sprint_task(
    task_id: str,
    req: SprintTaskToggleRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Mark daily sprint task complete/incomplete (FEAT-023)."""
    task = await CopilotService.toggle_sprint_task(db, current_user.id, task_id, req.is_completed)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sprint task not found.")
    return {"id": task.id, "is_completed": task.is_completed, "status": "updated"}

@router.post("/chat")
async def copilot_chat(
    req: CopilotChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Interactive multi-turn AI Mentor Q&A (FEAT-010, FEAT-017, FEAT-032)."""
    resp = await CopilotService.send_chat_message(
        db,
        current_user.id,
        message=req.message,
        session_id=req.session_id,
        persona=req.persona or "friendly_mentor",
        language=req.language or "en"
    )
    if "error" in resp:
        if resp["error"] == "RATE_LIMIT_EXCEEDED":
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=resp["detail"])
        elif resp["error"] == "PROMPT_SECURITY_VIOLATION":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=resp["detail"])
    return resp

@router.post("/chat/stream")
async def copilot_chat_stream(
    req: CopilotChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Realtime AI Streaming Support via SSE tokens (FEAT-013)."""
    from ai_engine.providers.factory import get_ai_provider
    from ai_engine.guardrails.sanitizer import sanitize_user_prompt
    from backend.app.services.context_aggregator import StudentContextAggregator

    is_safe, clean_prompt, reason = sanitize_user_prompt(req.message)
    if not is_safe:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)

    context = await StudentContextAggregator.aggregate_context(db, current_user.id)
    provider = get_ai_provider()

    async def token_generator():
        async for chunk in provider.stream_response(clean_prompt, context=context):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(token_generator(), media_type="text/event-stream")
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve chat history turns for a session (FEAT-010)."""
    history = await CopilotService.get_chat_history(db, current_user.id, session_id)
    return {"session_id": session_id, "messages": history}

@router.get("/chat/history/{session_id}")
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve chat history turns for a session (FEAT-010)."""
    history = await CopilotService.get_chat_history(db, current_user.id, session_id)
    return {"session_id": session_id, "messages": history}

@router.post("/feedback")
async def log_feedback(
    req: FeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Submit rating for an AI message (FEAT-015)."""
    ok = await CopilotService.log_feedback(db, current_user.id, req.message_id, req.rating)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found.")
    return {"status": "feedback_recorded"}

@router.get("/insights")
async def get_copilot_insights(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Fetch holistic placement analytics and readiness metrics (FEAT-016, FEAT-025, FEAT-035, FEAT-036)."""
    return await CopilotService.get_copilot_insights(db, current_user.id)

@router.get("/company-matrix/{company_name}")
async def get_company_matrix(
    company_name: str,
    current_user: User = Depends(get_current_user)
):
    """Fetch interview preparation matrix for a company (FEAT-024)."""
    return CopilotService.get_company_matrix(company_name)

@router.get("/trivia")
async def get_daily_trivia(
    current_user: User = Depends(get_current_user)
):
    """Get today's daily tech trivia micro-quiz (FEAT-039)."""
    return CopilotService.get_daily_trivia()

@router.post("/trivia/answer")
async def verify_trivia_answer(
    req: TriviaAnswerRequest,
    current_user: User = Depends(get_current_user)
):
    """Verify daily tech trivia answer (FEAT-039)."""
    return CopilotService.verify_trivia_answer(req.question_id, req.selected_option)

@router.get("/study-groups")
async def match_study_groups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Match student into relevant study circles (FEAT-040)."""
    return await CopilotService.match_study_groups(db, current_user.id)

@router.get("/weekly-digest")
async def get_weekly_digest(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Generate weekly summary report of hours spent, problems solved, and growth (FEAT-027)."""
    return await CopilotService.generate_weekly_digest(db, current_user.id)

@router.get("/eligibility-check")
async def check_placement_eligibility(
    min_cgpa: float = 6.5,
    max_backlogs: int = 0,
    min_attendance_pct: float = 75.0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Checks student GPA, backlogs, and attendance against configurable college placement rules (FEAT-038)."""
    return await CopilotService.check_placement_eligibility(
        db, current_user.id, min_cgpa, max_backlogs, min_attendance_pct
    )
