from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

# --- Deck Schemas ---
class FlashcardDeckCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: str = Field(default="General", max_length=100)
    tags: List[str] = Field(default_factory=list)
    is_public: bool = False

class FlashcardDeckUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None
    is_archived: Optional[bool] = None

class FlashcardDeckResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    category: str
    tags: List[str]
    is_public: bool
    is_system: bool
    is_approved: bool
    is_archived: bool
    share_slug: Optional[str] = None
    card_count: int = 0
    due_card_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Card Schemas ---
class FlashcardItemCreate(BaseModel):
    prompt: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    explanation: Optional[str] = None
    code_snippet: Optional[str] = None
    audio_url: Optional[str] = None
    order_index: int = 0

class FlashcardItemUpdate(BaseModel):
    prompt: Optional[str] = None
    answer: Optional[str] = None
    explanation: Optional[str] = None
    code_snippet: Optional[str] = None
    audio_url: Optional[str] = None
    order_index: Optional[int] = None

class FlashcardItemResponse(BaseModel):
    id: str
    deck_id: str
    prompt: str
    answer: str
    explanation: Optional[str] = None
    code_snippet: Optional[str] = None
    audio_url: Optional[str] = None
    order_index: int
    created_at: datetime
    # Review state if user studied
    repetition: Optional[int] = 0
    interval_days: Optional[int] = 0
    ease_factor: Optional[float] = 2.50
    stability: Optional[float] = 1.00
    next_review_at: Optional[datetime] = None
    is_due: bool = True

    class Config:
        from_attributes = True

# --- Review Submission Schemas ---
class CardReviewSubmitRequest(BaseModel):
    card_id: str
    grade: int = Field(..., ge=0, le=5)  # 0 to 5
    idempotency_key: str = Field(..., min_length=8, max_length=64)
    session_id: Optional[str] = None
    time_spent_ms: int = Field(default=0, ge=0)
    user_timezone: Optional[str] = "UTC"

class CardReviewSubmitResponse(BaseModel):
    idempotency_key: str
    card_id: str
    submitted_grade: int
    repetition: int
    interval_days: int
    ease_factor: float
    stability: float
    next_review_at: datetime
    is_replayed: bool = False

# --- Focus Session Schemas ---
class FocusSessionStartRequest(BaseModel):
    deck_id: Optional[str] = None
    duration_minutes: int = Field(default=25, ge=5, le=180)

class FocusSessionHeartbeatRequest(BaseModel):
    elapsed_seconds: int = Field(..., ge=0)
    cards_reviewed: int = Field(default=0, ge=0)
    status: str = "IN_PROGRESS"  # IN_PROGRESS, COMPLETED, ABORTED

class FocusSessionResponse(BaseModel):
    id: str
    user_id: str
    deck_id: Optional[str] = None
    duration_minutes: int
    elapsed_seconds: int
    cards_reviewed: int
    status: str
    started_at: datetime
    ended_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# --- Mistake Notebook Schemas ---
class MistakeEntryCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    source_type: str = "manual"  # manual, coding, assessment
    source_id: Optional[str] = None
    question_context: Optional[str] = None
    submitted_answer: Optional[str] = None
    expected_answer: Optional[str] = None
    error_message: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class MistakeEntryResponse(BaseModel):
    id: str
    user_id: str
    source_type: str
    source_id: Optional[str] = None
    title: str
    question_context: Optional[str] = None
    submitted_answer: Optional[str] = None
    expected_answer: Optional[str] = None
    error_message: Optional[str] = None
    tags: List[str]
    is_resolved: bool
    resolved_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- Heatmap and Stats Schemas ---
class HeatmapDayStat(BaseModel):
    date: str  # YYYY-MM-DD
    count: int

class RevisionDashboardStats(BaseModel):
    total_decks: int
    total_cards: int
    due_cards_count: int
    cards_reviewed_today: int
    retention_rate_pct: float
    current_streak_days: int
    heatmap: List[HeatmapDayStat]

# --- Anki Import / Export Schemas ---
class AnkiExportCard(BaseModel):
    prompt: str
    answer: str
    explanation: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class AnkiExportPayload(BaseModel):
    deck_title: str
    cards: List[AnkiExportCard]

class AnkiImportPayload(BaseModel):
    deck_title: Optional[str] = None
    title: Optional[str] = None
    category: Optional[str] = "General"
    description: Optional[str] = None
    cards: List[AnkiExportCard]
