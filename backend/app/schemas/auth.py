import enum
from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field, EmailStr

class UserRole(str, enum.Enum):
    STUDENT = "STUDENT"
    ADMIN = "ADMIN"
    PLACEMENT_CELL = "PLACEMENT_CELL"

class TokenPayload(BaseModel):
    sub: str
    role: UserRole
    exp: int
    iat: int
    type: str  # "access" or "refresh"

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    role: UserRole

class HealthResponse(BaseModel):
    status: str
    app: str
    environment: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    database: str
    ai_engine: str
    sandbox: str
