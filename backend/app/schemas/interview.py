from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class MockInterviewStartSchema(BaseModel):
    role_target: str = "Software Development Engineer"
    interview_type: str = "Technical"  # Technical, HR & Behavioral, System Design
    company_persona: str = "Google"  # Google, Amazon, TCS, etc.

class MockInterviewTurnResponseSchema(BaseModel):
    turn_index: int
    question_text: str
    question_category: str
    is_followup: bool = False

class MockInterviewSessionResponseSchema(BaseModel):
    session_id: str
    role_target: str
    interview_type: str
    company_persona: str
    status: str
    current_turn: MockInterviewTurnResponseSchema

class MockInterviewRespondSchema(BaseModel):
    response_text: str
    audio_duration_seconds: int = 0
    whiteboard_snapshot: Optional[Dict[str, Any]] = None

class MockInterviewEvaluationSchema(BaseModel):
    session_id: str
    role_target: str
    overall_readiness_score: float  # 0-100 (FEAT-117)
    star_scores: Dict[str, float]  # situation, task, action, result (FEAT-111)
    tone_clarity_score: float  # FEAT-112
    filler_word_count: int
    technical_accuracy_score: float  # FEAT-113
    pacing_verdict: str  # FEAT-118
    mistakes_and_blunders: List[str]  # FEAT-115
    improvement_plan: Dict[str, Any]  # FEAT-116
    transcript: List[Dict[str, Any]]  # FEAT-114
