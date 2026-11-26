from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# --- Discussion Threads ---
class ThreadCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    content: str = Field(..., min_length=5)
    category: str = Field(default="General", max_length=100)
    context_type: Optional[str] = None  # 'problem', 'topic', 'assessment', 'general'
    context_id: Optional[str] = None

class ThreadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    author_name: str
    title: str
    content: str
    category: str
    context_type: Optional[str] = None
    context_id: Optional[str] = None
    upvotes: int
    reply_count: int
    is_resolved: bool
    status: str
    created_at: datetime
    updated_at: datetime

# --- Discussion Replies ---
class ReplyCreate(BaseModel):
    content: str = Field(..., min_length=2)
    code_snippet: Optional[str] = None

class ReplyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    thread_id: str
    user_id: str
    author_name: str
    content: str
    code_snippet: Optional[str] = None
    upvotes: int
    is_accepted: bool
    status: str
    created_at: datetime

# --- Study Groups ---
class StudyGroupCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    goal_description: Optional[str] = None
    is_private: bool = False

class StudyGroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    creator_id: str
    name: str
    description: Optional[str] = None
    goal_description: Optional[str] = None
    is_private: bool
    invite_code: Optional[str] = None
    member_count: int
    is_member: bool = False
    created_at: datetime

class PeerLeaderboardEntry(BaseModel):
    user_id: str
    full_name: str
    karma_points: int
    accepted_answers: int
    threads_started: int
