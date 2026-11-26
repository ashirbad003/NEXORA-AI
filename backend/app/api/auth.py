from fastapi import APIRouter, Depends, Request, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db_session
from backend.app.schemas.user import (
    StudentRegisterRequest, LoginRequest, RefreshTokenRequest,
    TokenResponse, UserResponse
)
from backend.app.services.auth_service import AuthService
from backend.app.api.deps import get_current_user
from backend.app.models.auth import User
from backend.app.core.rate_limiter import rate_limiter

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register/student", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_student(
    req: StudentRegisterRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session)
):
    await rate_limiter.check_rate_limit(request, key_prefix="auth_register", limit=30, window_seconds=60)
    client_ip = request.client.host if request.client else None
    user = await AuthService.register_student(session, req, ip_address=client_ip)
    await session.commit()
    return user

@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session)
):
    await rate_limiter.check_rate_limit(request, key_prefix="auth_login", limit=60, window_seconds=60)
    client_ip = request.client.host if request.client else None
    user, access_token, refresh_token = await AuthService.authenticate_user(session, req, ip_address=client_ip)
    await session.commit()
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=15 * 60,
        user=user
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    req: RefreshTokenRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session)
):
    await rate_limiter.check_rate_limit(request, key_prefix="auth_refresh", limit=120, window_seconds=60)
    client_ip = request.client.host if request.client else None
    user, new_access, new_refresh = await AuthService.refresh_tokens(session, req.refresh_token, ip_address=client_ip)
    await session.commit()

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="bearer",
        expires_in=15 * 60,
        user=user
    )

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    req: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    await AuthService.revoke_refresh_token(session, req.refresh_token)
    await session.commit()
    return {"status": "ok", "message": "Successfully logged out."}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
