from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class QuestionCreateSchema(BaseModel):
    section_name: str = "General"
    order_index: int = 0
    question_text: str
    options: Dict[str, str]
    correct_option: str
    marks: float = 1.0
    explanation: Optional[str] = None
    topic_tag: str = "General"
    difficulty: str = "Medium"

class QuestionResponseSchema(BaseModel):
    id: str
    section_name: str
    order_index: int
    question_text: str
    options: Dict[str, str]
    marks: float
    topic_tag: str
    difficulty: str
    correct_option: Optional[str] = None
    explanation: Optional[str] = None

class AssessmentTestCreateSchema(BaseModel):
    title: str
    description: Optional[str] = None
    category: str = "Aptitude"
    difficulty: str = "Medium"
    duration_minutes: int = 30
    total_marks: float = 30.0
    pass_marks: float = 15.0
    negative_marking_rate: float = 0.25
    retake_allowed: bool = True
    retake_cooldown_hours: int = 24
    company_template: Optional[str] = None
    questions: Optional[List[QuestionCreateSchema]] = None

class AssessmentTestResponseSchema(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    category: str
    difficulty: str
    duration_minutes: int
    total_marks: float
    pass_marks: float
    negative_marking_rate: float
    retake_allowed: bool
    retake_cooldown_hours: int
    company_template: Optional[str] = None
    question_count: int = 0

class AnswerSaveSchema(BaseModel):
    question_id: str
    selected_option: Optional[str] = None
    time_spent_seconds: int = 0

class AnswerBatchSaveSchema(BaseModel):
    answers: List[AnswerSaveSchema]
    blur_count: Optional[int] = 0
    flagged_question_ids: Optional[List[str]] = None

class AttemptStartResponseSchema(BaseModel):
    attempt_id: str
    test_id: str
    duration_minutes: int
    remaining_seconds: int
    shuffled_questions: List[QuestionResponseSchema]
    saved_answers: Dict[str, str]
    flagged_question_ids: List[str]
    blur_count: int

class ScorecardResponseSchema(BaseModel):
    attempt_id: str
    test_title: str
    status: str
    score: float
    total_marks: float
    accuracy_percentage: float
    percentile: float
    time_taken_seconds: int
    total_questions: int
    correct_count: int
    incorrect_count: int
    unattempted_count: int
    section_breakdown: Dict[str, Any]
    weak_topic_tags: List[str]
    solution_keys: List[Dict[str, Any]]
