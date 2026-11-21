from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db_session
from backend.app.api.deps import get_current_user, require_roles
from backend.app.models.auth import User
from backend.app.schemas.user import UserRoleEnum
from backend.app.schemas.phase9_portals import (
    PlacementDriveCreateRequest, PlacementDriveResponse,
    DriveRegisterRequest, DriveRegistrationResponse,
    RegistrationStatusUpdateRequest, OfferCreateRequest, OfferResponse,
    StudentPlacementProfileResponse, BlacklistUpdateRequest, OptOutUpdateRequest,
    InstitutionalDashboardStats
)
from backend.app.services.placement_service import PlacementCellService

router = APIRouter(prefix="/placement-cell", tags=["Placement Cell Intelligence (Phase 9)"])

@router.get("/drives", response_model=List[PlacementDriveResponse])
async def list_placement_drives(
    status_filter: Optional[str] = Query(None, description="Scheduled, Ongoing, Completed"),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    return await PlacementCellService.list_drives(session, status_filter)

@router.post("/drives", response_model=PlacementDriveResponse, status_code=status.HTTP_201_CREATED)
async def create_placement_drive(
    payload: PlacementDriveCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    officer: User = Depends(require_roles([UserRoleEnum.PLACEMENT_CELL, UserRoleEnum.ADMIN]))
):
    return await PlacementCellService.create_drive(session, payload)

@router.post("/drives/{drive_id}/register", response_model=DriveRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register_for_drive(
    drive_id: str,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    return await PlacementCellService.register_student_for_drive(session, current_user.id, drive_id)

@router.patch("/registrations/{registration_id}", response_model=DriveRegistrationResponse)
async def update_registration_status(
    registration_id: str,
    payload: RegistrationStatusUpdateRequest,
    session: AsyncSession = Depends(get_db_session),
    officer: User = Depends(require_roles([UserRoleEnum.PLACEMENT_CELL, UserRoleEnum.ADMIN]))
):
    return await PlacementCellService.update_registration_status(session, registration_id, payload)

@router.post("/offers", response_model=OfferResponse, status_code=status.HTTP_201_CREATED)
async def extend_offer(
    payload: OfferCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    officer: User = Depends(require_roles([UserRoleEnum.PLACEMENT_CELL, UserRoleEnum.ADMIN]))
):
    return await PlacementCellService.extend_offer(session, payload)

@router.post("/students/{student_id}/blacklist", response_model=StudentPlacementProfileResponse)
async def update_blacklist_status(
    student_id: str,
    payload: BlacklistUpdateRequest,
    session: AsyncSession = Depends(get_db_session),
    officer: User = Depends(require_roles([UserRoleEnum.PLACEMENT_CELL, UserRoleEnum.ADMIN]))
):
    return await PlacementCellService.set_blacklist(session, student_id, payload)

@router.get("/analytics/institutional", response_model=InstitutionalDashboardStats)
async def get_institutional_analytics(
    session: AsyncSession = Depends(get_db_session),
    officer: User = Depends(require_roles([UserRoleEnum.PLACEMENT_CELL, UserRoleEnum.ADMIN]))
):
    return await PlacementCellService.get_institutional_analytics(session)
