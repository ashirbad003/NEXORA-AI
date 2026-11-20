from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.db.session import get_db_session
from backend.app.api.deps import require_roles
from backend.app.models.auth import User, AuditLog
from backend.app.schemas.user import UserResponse, AuditLogResponse, UserRoleEnum

router = APIRouter(prefix="/admin", tags=["Admin Domain"])

@router.get("/users", response_model=List[UserResponse])
async def list_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
    admin_user: User = Depends(require_roles([UserRoleEnum.ADMIN]))
):
    stmt = select(User).offset(skip).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()

@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    action: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_db_session),
    admin_user: User = Depends(require_roles([UserRoleEnum.ADMIN]))
):
    stmt = select(AuditLog)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    stmt = stmt.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()
