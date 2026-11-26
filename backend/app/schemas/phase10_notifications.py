from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# --- User Notifications ---
class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    category: str
    urgency: str
    title: str
    message: str
    action_url: Optional[str] = None
    payload: Dict[str, Any]
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

class NotificationPreferencesUpdate(BaseModel):
    in_app_enabled: Optional[bool] = None
    email_enabled: Optional[bool] = None
    push_enabled: Optional[bool] = None
    category_overrides: Optional[Dict[str, Any]] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None

class NotificationPreferencesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    in_app_enabled: bool
    email_enabled: bool
    push_enabled: bool
    category_overrides: Dict[str, Any]
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None

class NotificationCreateInternal(BaseModel):
    user_id: str
    category: str = "GENERAL"  # REVISION, COMMUNITY, SYSTEM, PLACEMENT
    urgency: str = "NORMAL"    # LOW, NORMAL, HIGH, CRITICAL
    title: str
    message: str
    action_url: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
