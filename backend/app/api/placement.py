from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.db.session import get_db_session
from backend.app.api.deps import require_roles
from backend.app.models.auth import User, StudentProfile
from backend.app.schemas.user import StudentProfileResponse, UserRoleEnum

router = APIRouter(prefix="/placement", tags=["Placement Cell Domain"])

@router.get("/students", response_model=List[StudentProfileResponse])
async def list_placement_students(
    department: Optional[str] = Query(None, description="Filter by department"),
    batch_year: Optional[int] = Query(None, description="Filter by batch year"),
    min_cgpa: Optional[float] = Query(None, ge=0.0, le=10.0, description="Filter by minimum CGPA"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    placement_user: User = Depends(require_roles([UserRoleEnum.PLACEMENT_CELL, UserRoleEnum.ADMIN]))
):
    stmt = select(StudentProfile)
    if department:
        stmt = stmt.where(StudentProfile.department == department)
    if batch_year:
        stmt = stmt.where(StudentProfile.batch_year == batch_year)
    if min_cgpa is not None:
        stmt = stmt.where(StudentProfile.cgpa >= min_cgpa)
    stmt = stmt.offset(skip).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()
