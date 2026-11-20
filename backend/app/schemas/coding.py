from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class TestCaseSampleResponse(BaseModel):
    id: str
    stdin_input: str
    expected_output: str
    explanation: Optional[str] = None
    order_index: int
    model_config = ConfigDict(from_attributes=True)

class CodingProblemListItem(BaseModel):
    id: str
    slug: str
    title: str
    difficulty: str
    category: str
    tags: Optional[str] = None
    companies: Optional[str] = None
    time_limit_ms: int
    memory_limit_mb: int
    model_config = ConfigDict(from_attributes=True)

class CodingProblemDetailResponse(CodingProblemListItem):
    description_markdown: str
    constraints: Optional[str] = None
    starter_code_python: Optional[str] = None
    starter_code_java: Optional[str] = None
    starter_code_cpp: Optional[str] = None
    starter_code_c: Optional[str] = None
    sample_test_cases: List[TestCaseSampleResponse] = []
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class CodingProblemListResponse(BaseModel):
    problems: List[CodingProblemListItem]
    total: int

class CodeRunRequest(BaseModel):
    language: str = Field(..., description="python, java, cpp, or c")
    code: str
    custom_input: Optional[str] = ""

class CodeRunResponse(BaseModel):
    language: str
    status: str
    stdout: str
    stderr: Optional[str] = ""
    execution_time_ms: float
    memory_used_mb: float
    is_timeout: bool = False
    isolation_boundary: str

class CodeSubmitRequest(BaseModel):
    language: str = Field(..., description="python, java, cpp, or c")
    code: str

class SubmissionResultResponse(BaseModel):
    id: str
    problem_id: str
    problem_slug: str
    problem_title: str
    language: str
    verdict: str  # ACCEPTED, WRONG_ANSWER, TIME_LIMIT_EXCEEDED, COMPILATION_ERROR, EXECUTION_BLOCKED_SECURITY_POLICY
    passed_test_cases: int
    total_test_cases: int
    execution_time_ms: float
    memory_used_mb: float
    error_message: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class StudentCodingStatsResponse(BaseModel):
    user_id: str
    total_solved: int
    easy_solved: int
    medium_solved: int
    hard_solved: int
    current_streak_days: int
    longest_streak_days: int
    last_solved_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
