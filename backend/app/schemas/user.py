import enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, ConfigDict

class UserRoleEnum(str, enum.Enum):
    STUDENT = "STUDENT"
    ADMIN = "ADMIN"
    PLACEMENT_CELL = "PLACEMENT_CELL"

# Request Schemas
class StudentRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=100)
    phone_number: Optional[str] = Field(default=None, max_length=20)
    institution: Optional[str] = Field(default=None, max_length=200)
    department: Optional[str] = Field(default=None, max_length=100)
    batch_year: Optional[int] = Field(default=None, ge=2000, le=2050)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)

# Response Schemas
class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    description: Optional[str] = None

class StudentProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    institution: Optional[str] = None
    department: Optional[str] = None
    batch_year: Optional[int] = None
    cgpa: Optional[float] = None
    skills: Optional[str] = None
    career_preferences: Optional[str] = None
    readiness_score: int = 0

class StudentProfileUpdateRequest(BaseModel):
    institution: Optional[str] = Field(default=None, max_length=200)
    department: Optional[str] = Field(default=None, max_length=100)
    batch_year: Optional[int] = Field(default=None, ge=2000, le=2050)
    cgpa: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    skills: Optional[str] = Field(default=None, max_length=1000)
    career_preferences: Optional[str] = Field(default=None, max_length=1000)

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: EmailStr
    full_name: str
    phone_number: Optional[str] = None
    is_active: bool
    is_email_verified: bool
    created_at: datetime
    roles: List[RoleResponse] = []
    student_profile: Optional[StudentProfileResponse] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    details: Optional[str] = None
    created_at: datetime
