from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db_session
from backend.app.api.deps import require_roles
from backend.app.models.auth import User
from backend.app.schemas.user import UserRoleEnum
from backend.app.schemas.phase9_portals import (
    FeatureFlagUpdateRequest, FeatureFlagResponse, SystemHealthTelemetry,
    DiagnosticReportResponse
)
from backend.app.services.admin_intelligence_service import AdminIntelligenceService

router = APIRouter(prefix="/admin-intelligence", tags=["Super Admin Intelligence (Phase 9)"])

@router.get("/flags", response_model=List[FeatureFlagResponse])
async def list_feature_flags(
    session: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_roles([UserRoleEnum.ADMIN]))
):
    return await AdminIntelligenceService.list_feature_flags(session)

@router.post("/flags", response_model=FeatureFlagResponse)
async def update_feature_flag(
    payload: FeatureFlagUpdateRequest,
    session: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_roles([UserRoleEnum.ADMIN]))
):
    return await AdminIntelligenceService.get_or_create_feature_flag(session, payload, admin.id)

@router.get("/telemetry", response_model=SystemHealthTelemetry)
async def get_system_telemetry(
    session: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_roles([UserRoleEnum.ADMIN]))
):
    return await AdminIntelligenceService.get_system_telemetry(session)

@router.post("/diagnostics/generate", response_model=DiagnosticReportResponse)
async def generate_diagnostic_report(
    session: AsyncSession = Depends(get_db_session),
    admin: User = Depends(require_roles([UserRoleEnum.ADMIN]))
):
    return await AdminIntelligenceService.generate_diagnostic_report(session)
