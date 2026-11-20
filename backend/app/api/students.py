from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.db.session import get_db_session
from backend.app.api.deps import get_current_user, require_roles
from backend.app.models.auth import User, StudentProfile
from backend.app.schemas.user import (
    UserResponse,
    StudentProfileResponse,
    StudentProfileUpdateRequest,
    UserRoleEnum
)

router = APIRouter(prefix="/students", tags=["Student Domain"])

def compute_readiness_score(profile: StudentProfile) -> int:
    """
    Computes an initial readiness score (0-100) based on profile completeness and CGPA:
    - Base completeness: 40 points
    - CGPA weight: up to 30 points
    - Skills listed: up to 20 points
    - Career preferences: 10 points
    """
    score = 0
    if profile.institution and profile.department and profile.batch_year:
        score += 40
    if profile.cgpa is not None:
        score += int(min(30, (profile.cgpa / 10.0) * 30))
    if profile.skills and len(profile.skills.strip()) > 0:
        skill_count = len([s for s in profile.skills.split(",") if s.strip()])
        score += min(20, skill_count * 4)
    if profile.career_preferences and len(profile.career_preferences.strip()) > 0:
        score += 10
    return min(100, max(0, score))

@router.get("/profile/{student_user_id}", response_model=StudentProfileResponse)
async def get_student_profile(
    student_user_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    """
    IDOR-Protected Profile Access:
    - Students may ONLY view their own profile.
    - ADMIN and PLACEMENT_CELL may view any student profile.
    """
    user_role_names = {r.name for r in current_user.roles}
    is_staff = bool(user_role_names.intersection({UserRoleEnum.ADMIN.value, UserRoleEnum.PLACEMENT_CELL.value}))

    if not is_staff and current_user.id != student_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You cannot view another student's profile."
        )

    stmt = select(StudentProfile).where(StudentProfile.user_id == student_user_id)
    result = await session.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found.")

    return profile

@router.get("/my-profile", response_model=StudentProfileResponse)
async def get_my_profile(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles([UserRoleEnum.STUDENT]))
):
    stmt = select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    result = await session.execute(stmt)
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found.")
    return profile

@router.put("/my-profile", response_model=StudentProfileResponse)
async def update_my_profile(
    update_data: StudentProfileUpdateRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_roles([UserRoleEnum.STUDENT]))
):
    stmt = select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    result = await session.execute(stmt)
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found.")

    # Apply updates
    if update_data.institution is not None:
        profile.institution = update_data.institution
    if update_data.department is not None:
        profile.department = update_data.department
    if update_data.batch_year is not None:
        profile.batch_year = update_data.batch_year
    if update_data.cgpa is not None:
        profile.cgpa = update_data.cgpa
    if update_data.skills is not None:
        profile.skills = update_data.skills
    if update_data.career_preferences is not None:
        profile.career_preferences = update_data.career_preferences

    # Recompute readiness score
    profile.readiness_score = compute_readiness_score(profile)

    await session.commit()
    await session.refresh(profile)
    return profile
