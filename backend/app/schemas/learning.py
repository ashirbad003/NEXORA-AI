from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

class LearningModuleBase(BaseModel):
    slug: str
    title: str
    category: str
    summary: str
    content_markdown: str
    estimated_read_time_minutes: int = 5
    difficulty_level: str = "Medium"
    prerequisites: Optional[str] = None
    order_index: int = 0
    is_published: bool = True

class LearningModuleResponse(LearningModuleBase):
    id: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class LearningModuleListResponse(BaseModel):
    modules: List[LearningModuleResponse]
    total: int

class TopicProgressUpdate(BaseModel):
    is_completed: bool = True
    mastery_score: int = Field(default=100, ge=0, le=100)

class TopicProgressResponse(BaseModel):
    id: str
    user_id: str
    module_id: str
    is_completed: bool
    mastery_score: int
    last_studied_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TopicNoteCreate(BaseModel):
    note_content: str
    is_bookmarked: bool = False

class TopicNoteResponse(BaseModel):
    id: str
    user_id: str
    module_id: str
    note_content: str
    is_bookmarked: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# FEAT-126: AI Concept Tutor (Socratic Mode)
class SocraticTutorRequest(BaseModel):
    concept_slug: str
    student_query: str
    conversation_history: List[Dict[str, str]] = []

class SocraticTutorResponse(BaseModel):
    concept_slug: str
    socratic_guidance: str
    guiding_question: str
    suggested_focus_areas: List[str]

# FEAT-127: Interactive Code Snippet Sandbox (Deterministic Simulator)
class CodeSnippetSimRequest(BaseModel):
    language: str = Field(..., description="python, javascript, cpp, or java")
    code: str
    stdin: Optional[str] = None

class CodeSnippetSimResponse(BaseModel):
    language: str
    status: str
    stdout: str
    execution_time_ms: float
    simulated: bool
    ast_analysis: Dict[str, Any]

# FEAT-130: Curated Video & Visual Resources
class VisualResource(BaseModel):
    id: str
    title: str
    platform: str
    duration: str
    embed_url: str
    summary: str

# FEAT-131: Practice Problem Linker
class PracticeProblem(BaseModel):
    id: str
    title: str
    difficulty: str
    category: str
    coding_arena_slug: str
    target_skill: str

# FEAT-132: Downloadable Concept Cheat Sheets
class CheatSheetResponse(BaseModel):
    slug: str
    title: str
    summary_markdown: str
    complexity_table: Dict[str, str]
    key_takeaways: List[str]
    code_reference: str

# FEAT-133: Multilingual Translations
class MultilingualContentResponse(BaseModel):
    slug: str
    language: str
    title: str
    summary: str
    content_markdown: str

# FEAT-135: Topic Difficulty Feedback
class TopicFeedbackCreate(BaseModel):
    difficulty_rating: int = Field(..., ge=1, le=5, description="1 (Very Easy) to 5 (Very Hard)")
    confusing_sections: Optional[str] = None
    feedback_text: Optional[str] = None

class TopicFeedbackResponse(BaseModel):
    id: str
    user_id: str
    module_id: str
    difficulty_rating: int
    confusing_sections: Optional[str] = None
    feedback_text: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# FEAT-137: Real-World Architecture Case Studies
class ArchitectureCaseStudy(BaseModel):
    id: str
    system_name: str
    title: str
    scale_metrics: str
    architecture_overview: str
    dsa_patterns_used: List[str]
    deep_dive_markdown: str

# FEAT-138: Interactive Flash Quiz Checkpoints
class FlashQuizQuestion(BaseModel):
    id: str
    question: str
    options: List[str]
    correct_option_index: int
    explanation: str

class FlashQuizResponse(BaseModel):
    slug: str
    questions: List[FlashQuizQuestion]

class FlashQuizSubmitRequest(BaseModel):
    answers: Dict[str, int]  # question_id -> selected_option_index

class FlashQuizResultResponse(BaseModel):
    score: int
    total_questions: int
    percentage: float
    passed: bool
    review: List[Dict[str, Any]]

# FEAT-144: Curriculum Versioning & Changelog
class CurriculumChangelogEntry(BaseModel):
    version: str
    released_at: str
    changes: List[str]
    affected_topics: List[str]

# Algorithm Simulation Schemas (DSAVIZ)
class GraphTraversalRequest(BaseModel):
    algorithm: str = Field(..., description="bfs or dfs")
    nodes: List[str]
    edges: List[List[str]]
    start_node: str

class ShortestPathRequest(BaseModel):
    algorithm: str = Field(..., description="dijkstra or bellman_ford")
    nodes: List[str]
    edges: List[Dict[str, Any]]
    start_node: str

class AlgorithmStep(BaseModel):
    step_number: int
    current_node: Optional[str] = None
    visited_nodes: List[str] = []
    frontier: List[str] = []
    description: str
    state_snapshot: Dict[str, Any] = {}

class AlgorithmTraceResponse(BaseModel):
    algorithm: str
    total_steps: int
    steps: List[AlgorithmStep]
    result: Dict[str, Any]
