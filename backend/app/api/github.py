from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db_session
from backend.app.api.deps import get_current_user
from backend.app.models.auth import User
from backend.app.schemas.phase8_intelligence import (
    GitHubScanRequest, GitHubProfileResponse
)
from backend.app.services.github_service import GitHubIntelligenceService

router = APIRouter(prefix="/github", tags=["GitHub Portfolio Intelligence (Phase 8)"])

@router.post("/scan", response_model=GitHubProfileResponse)
async def scan_github_profile(
    payload: GitHubScanRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    return await GitHubIntelligenceService.scan_and_cache_profile(
        session, current_user.id, payload.github_username
    )

@router.get("/profile", response_model=GitHubProfileResponse)
async def get_github_profile(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    profile = await GitHubIntelligenceService.get_cached_profile(session, current_user.id)
    if not profile:
        # Scan default profile if none exists
        default_handle = (current_user.email.split("@")[0]) if current_user.email else "nexora-developer"
        return await GitHubIntelligenceService.scan_and_cache_profile(
            session, current_user.id, default_handle
        )
    return profile
