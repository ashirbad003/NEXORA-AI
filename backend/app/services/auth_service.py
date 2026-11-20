import hashlib
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from backend.app.core.security import (
    hash_password, verify_password, create_access_token, create_refresh_token, decode_token
)
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models.auth import (
    User, Role, StudentProfile, RefreshToken, AuditLog
)
from backend.app.schemas.user import (
    StudentRegisterRequest, LoginRequest, UserRoleEnum
)

def _hash_token_string(token: str) -> str:
    """Secure hash of refresh token for safe database persistence"""
    return hashlib.sha256(token.encode('utf-8')).hexdigest()

def _ensure_utc(dt: datetime) -> datetime:
    """Ensure datetime has timezone.utc for safe comparison across SQLite / PostgreSQL"""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

class AuthService:
    @staticmethod
    async def get_or_create_role(session: AsyncSession, role_name: str) -> Role:
        stmt = select(Role).where(Role.name == role_name)
        result = await session.execute(stmt)
        role = result.scalar_one_or_none()
        if not role:
            role = Role(
                id=str(uuid.uuid4()),
                name=role_name,
                description=f"System role for {role_name}"
            )
            session.add(role)
            await session.flush()
        return role

    @staticmethod
    async def log_audit(
        session: AsyncSession,
        user_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[dict] = None
    ) -> AuditLog:
        audit = AuditLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            details=json.dumps(details) if details else None,
            created_at=datetime.now(timezone.utc)
        )
        session.add(audit)
        await session.flush()
        return audit

    @staticmethod
    async def register_student(
        session: AsyncSession,
        req: StudentRegisterRequest,
        ip_address: Optional[str] = None
    ) -> User:
        # Check if email already registered
        stmt = select(User).where(User.email == req.email.lower())
        existing = await session.execute(stmt)
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A user with this email address already exists."
            )

        # Hash password with Argon2id
        hashed_pwd = hash_password(req.password)
        user_id = str(uuid.uuid4())

        user = User(
            id=user_id,
            email=req.email.lower(),
            full_name=req.full_name,
            phone_number=req.phone_number,
            hashed_password=hashed_pwd,
            is_active=True,
            is_email_verified=False,
            created_at=datetime.now(timezone.utc)
        )

        # Attach STUDENT role
        student_role = await AuthService.get_or_create_role(session, UserRoleEnum.STUDENT.value)
        user.roles.append(student_role)

        # Create StudentProfile
        profile = StudentProfile(
            id=str(uuid.uuid4()),
            user_id=user_id,
            institution=req.institution,
            department=req.department,
            batch_year=req.batch_year,
            readiness_score=0
        )
        user.student_profile = profile

        session.add(user)
        session.add(profile)
        await session.flush()

        # Audit log registration
        await AuthService.log_audit(
            session=session,
            user_id=user_id,
            action="STUDENT_REGISTER",
            resource_type="USER",
            resource_id=user_id,
            ip_address=ip_address,
            details={"email": req.email.lower(), "role": "STUDENT"}
        )

        return user

    @staticmethod
    async def authenticate_user(
        session: AsyncSession,
        req: LoginRequest,
        ip_address: Optional[str] = None
    ) -> Tuple[User, str, str]:
        stmt = select(User).where(User.email == req.email.lower())
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not verify_password(req.password, user.hashed_password):
            # Log failed attempt
            await AuthService.log_audit(
                session=session,
                user_id=user.id if user else None,
                action="LOGIN_FAILED",
                resource_type="USER",
                ip_address=ip_address,
                details={"attempted_email": req.email.lower()}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password."
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated. Contact platform administrator."
            )

        # Determine primary role
        primary_role = user.roles[0].name if user.roles else UserRoleEnum.STUDENT.value

        # Generate access and refresh tokens
        access_token = create_access_token(user.id, primary_role)
        refresh_token = create_refresh_token(user.id, primary_role)

        # Store refresh token hash in DB
        token_hash = _hash_token_string(refresh_token)
        exp_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        expires_at = datetime.now(timezone.utc) + exp_delta

        rt = RefreshToken(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=False
        )
        session.add(rt)

        # Update last login
        user.last_login_at = datetime.now(timezone.utc)
        await session.flush()

        await AuthService.log_audit(
            session=session,
            user_id=user.id,
            action="LOGIN_SUCCESS",
            resource_type="SESSION",
            ip_address=ip_address
        )

        return user, access_token, refresh_token

    @staticmethod
    async def refresh_tokens(
        session: AsyncSession,
        raw_refresh_token: str,
        ip_address: Optional[str] = None
    ) -> Tuple[User, str, str]:
        try:
            payload = decode_token(raw_refresh_token)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token."
            )

        if payload.type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is not a valid refresh token."
            )

        token_hash = _hash_token_string(raw_refresh_token)

        # Atomic claim: set is_revoked = True WHERE token_hash = :hash AND is_revoked = False
        from sqlalchemy import update
        claim_stmt = (
            update(RefreshToken)
            .where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.is_revoked == False
            )
            .values(is_revoked=True)
        )
        claim_res = await session.execute(claim_stmt)
        await session.flush()

        if claim_res.rowcount == 0:
            # Token does not exist or was already claimed/revoked!
            # Check if this token exists in revoked state (token reuse attack)
            stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
            result = await session.execute(stmt)
            stored_token = result.scalar_one_or_none()

            if stored_token and stored_token.is_revoked:
                logger.warning(f"Refresh token reuse detected for user {payload.sub}!")
                revoke_stmt = select(RefreshToken).where(RefreshToken.user_id == payload.sub)
                res = await session.execute(revoke_stmt)
                for t in res.scalars():
                    t.is_revoked = True
                await session.commit()

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked or is invalid."
            )

        # Now fetch the token metadata to verify expiration
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await session.execute(stmt)
        stored_token = result.scalar_one()

        if _ensure_utc(stored_token.expires_at) < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired."
            )

        # Fetch user
        stmt_user = select(User).where(User.id == payload.sub)
        res_user = await session.execute(stmt_user)
        user = res_user.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive.")

        primary_role = user.roles[0].name if user.roles else UserRoleEnum.STUDENT.value
        new_access = create_access_token(user.id, primary_role)
        new_refresh = create_refresh_token(user.id, primary_role)

        new_rt = RefreshToken(
            id=str(uuid.uuid4()),
            user_id=user.id,
            token_hash=_hash_token_string(new_refresh),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            is_revoked=False
        )
        session.add(new_rt)
        await session.flush()

        await AuthService.log_audit(
            session=session,
            user_id=user.id,
            action="TOKEN_REFRESH",
            resource_type="SESSION",
            ip_address=ip_address
        )

        return user, new_access, new_refresh

    @staticmethod
    async def revoke_refresh_token(session: AsyncSession, raw_refresh_token: str) -> bool:
        token_hash = _hash_token_string(raw_refresh_token)
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        res = await session.execute(stmt)
        token = res.scalar_one_or_none()
        if token:
            token.is_revoked = True
            await session.flush()
            return True
        return False
