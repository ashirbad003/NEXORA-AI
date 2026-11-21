from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class CareerPathSelectRequest(BaseModel):
    target_role: str = Field(default="Software Development Engineer")
    target_companies: List[str] = Field(default_factory=list)
    target_salary_min_lpa: float = Field(default=12.0)
    target_salary_max_lpa: float = Field(default=25.0)
    preferred_persona: str = Field(default="friendly_mentor")
    preferred_language: str = Field(default="en")

class CareerPathResponse(BaseModel):
    target_role: str
    target_companies: List[str]
    target_salary_min_lpa: float
    target_salary_max_lpa: float
    preferred_persona: str
    preferred_language: str
    updated_at: datetime

class RoadmapGenerateRequest(BaseModel):
    target_role: Optional[str] = None
    force_regenerate: bool = False

class SprintTaskToggleRequest(BaseModel):
    is_completed: bool

class CopilotChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: Optional[str] = None
    persona: Optional[str] = None
    language: Optional[str] = "en"

class FeedbackRequest(BaseModel):
    message_id: str
    rating: int = Field(..., ge=-1, le=1) # 1 = up, -1 = down
    comment: Optional[str] = None

class TriviaAnswerRequest(BaseModel):
    question_id: str
    selected_option: int
