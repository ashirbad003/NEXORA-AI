from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict


# ==========================================
# 1. Device Registration Schemas
# ==========================================

class DeviceTokenRegisterRequest(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=100, description="Client-generated unique hardware UUID")
    expo_push_token: str = Field(..., min_length=1, max_length=255, description="Expo push notification token")
    device_os: str = Field("ANDROID", max_length=32, description="Device OS (ANDROID, IOS)")
    device_model: Optional[str] = Field(None, max_length=100, description="Device model string")
    app_version: str = Field("1.0.0", max_length=32, description="Client app semantic version")


class DeviceTokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    device_id: str
    expo_push_token: str
    device_os: str
    device_model: Optional[str] = None
    app_version: str
    is_active: bool
    created_at: datetime
    last_used_at: datetime


# ==========================================
# 2. Sync Push Schemas (Offline Mutations)
# ==========================================

class SyncPushOperation(BaseModel):
    op_id: str = Field(..., min_length=1, max_length=64, description="Client idempotency key UUID")
    action_type: str = Field(..., description="Action type: SUBMIT_CARD_REVIEW, RESOLVE_MISTAKE, etc.")
    client_timestamp: datetime = Field(..., description="Client time when the action was performed offline")
    payload: Dict[str, Any] = Field(..., description="Action-specific payload parameters")


class SyncPushRequest(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=100)
    operations: List[SyncPushOperation] = Field(..., max_length=50)


class SyncOperationResult(BaseModel):
    op_id: str
    status: str  # "SUCCESS", "SUPERSEDED", "REPLAYED", "REJECTED"
    message: Optional[str] = None
    card_id: Optional[str] = None
    repetition: Optional[int] = None
    interval_days: Optional[int] = None
    ease_factor: Optional[float] = None
    stability: Optional[float] = None
    next_review_at: Optional[str] = None
    resulting_state_version: Optional[int] = None
    is_replayed: bool = False
    is_superseded: bool = False


class SyncPushResponse(BaseModel):
    device_id: str
    processed_count: int
    results: List[SyncOperationResult]
    new_server_seq: int


# ==========================================
# 3. Sync Pull Schemas (Delta Sync)
# ==========================================

class ChangeFeedItem(BaseModel):
    change_seq: int
    entity_type: str
    entity_id: str
    operation: str
    payload: Dict[str, Any]
    created_at: datetime


class SyncPullResponse(BaseModel):
    server_seq: int
    has_more: bool
    deltas: List[ChangeFeedItem]
    tombstones: List[Dict[str, Any]]


# ==========================================
# 4. Sync Snapshot Schemas (Full Resync)
# ==========================================

class SyncSnapshotResponse(BaseModel):
    snapshot_seq: int
    decks: List[Dict[str, Any]]
    due_cards: List[Dict[str, Any]]
    readiness_score: int
    mistakes: List[Dict[str, Any]]
    generated_at: datetime
