import unittest
import os
import sys
import asyncio
import uuid
import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from backend.app.db.session import Base, get_db_session
from backend.app.models.auth import User, Role, StudentProfile, RefreshToken, AuditLog
from backend.app.schemas.user import UserRoleEnum
from backend.app.services.auth_service import AuthService
from backend.app.main import app

TEST_DB_URL = "sqlite+aiosqlite:///./test_phase2_suite.db"

class TestPhase2AuthAndRBAC(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine(TEST_DB_URL, echo=False)
        self.AsyncSessionLocal = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )
        # Create all tables cleanly
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
            
        # Override FastAPI get_db_session dependency to use test database session
        async def override_get_db_session():
            async with self.AsyncSessionLocal() as session:
                try:
                    yield session
                except Exception:
                    await session.rollback()
                    raise
                finally:
                    await session.close()

        app.dependency_overrides[get_db_session] = override_get_db_session

        self.transport = httpx.ASGITransport(app=app)
        self.base_url = "http://testserver"

    async def asyncTearDown(self):
        app.dependency_overrides.clear()
        await self.engine.dispose()
        if os.path.exists("./test_phase2_suite.db"):
            try:
                os.remove("./test_phase2_suite.db")
            except Exception:
                pass

    async def test_01_student_registration_and_argon2_hash(self):
        async with self.AsyncSessionLocal() as session:
            from backend.app.schemas.user import StudentRegisterRequest
            req = StudentRegisterRequest(
                email="alice.student@nexora.ai",
                password="SecurePassword2026!",
                full_name="Alice Student",
                department="Computer Science",
                batch_year=2026
            )
            user = await AuthService.register_student(session, req)
            await session.commit()

            self.assertEqual(user.email, "alice.student@nexora.ai")
            self.assertTrue(user.hashed_password.startswith("$argon2id$"))
            self.assertEqual(len(user.roles), 1)
            self.assertEqual(user.roles[0].name, UserRoleEnum.STUDENT.value)
            self.assertIsNotNone(user.student_profile)
            self.assertEqual(user.student_profile.department, "Computer Science")

    async def test_02_duplicate_registration_rejected(self):
        async with self.AsyncSessionLocal() as session:
            from backend.app.schemas.user import StudentRegisterRequest
            req = StudentRegisterRequest(
                email="duplicate@nexora.ai",
                password="SecurePassword2026!",
                full_name="Duplicate User"
            )
            await AuthService.register_student(session, req)
            await session.commit()

            with self.assertRaises(Exception) as ctx:
                await AuthService.register_student(session, req)
            self.assertIn("already exists", str(ctx.exception))

    async def test_03_login_and_token_rotation(self):
        async with self.AsyncSessionLocal() as session:
            from backend.app.schemas.user import StudentRegisterRequest, LoginRequest
            # Register
            reg_req = StudentRegisterRequest(
                email="bob.student@nexora.ai",
                password="BobPassword#2026",
                full_name="Bob Student"
            )
            user = await AuthService.register_student(session, reg_req)
            await session.commit()

            # Login
            login_req = LoginRequest(email="bob.student@nexora.ai", password="BobPassword#2026")
            logged_user, access_token, refresh_token = await AuthService.authenticate_user(session, login_req)
            await session.commit()

            self.assertIsNotNone(access_token)
            self.assertIsNotNone(refresh_token)
            self.assertIsNotNone(logged_user.last_login_at)

            # Refresh token rotation
            refreshed_user, new_access, new_refresh = await AuthService.refresh_tokens(session, refresh_token)
            await session.commit()

            self.assertNotEqual(access_token, new_access)
            self.assertNotEqual(refresh_token, new_refresh)

            # Verify that old refresh token is now revoked and cannot be reused
            with self.assertRaises(Exception) as ctx:
                await AuthService.refresh_tokens(session, refresh_token)
            self.assertIn("revoked or is invalid", str(ctx.exception))

    async def test_04_invalid_credentials_fail(self):
        async with self.AsyncSessionLocal() as session:
            from backend.app.schemas.user import StudentRegisterRequest, LoginRequest
            reg_req = StudentRegisterRequest(
                email="charlie@nexora.ai",
                password="CorrectPassword2026",
                full_name="Charlie"
            )
            await AuthService.register_student(session, reg_req)
            await session.commit()

            with self.assertRaises(Exception) as ctx:
                await AuthService.authenticate_user(
                    session,
                    LoginRequest(email="charlie@nexora.ai", password="WrongPassword999")
                )
            self.assertIn("Invalid email or password", str(ctx.exception))

    async def test_05_audit_log_recorded(self):
        async with self.AsyncSessionLocal() as session:
            from backend.app.schemas.user import StudentRegisterRequest
            reg_req = StudentRegisterRequest(
                email="diana@nexora.ai",
                password="DianaPassword2026",
                full_name="Diana"
            )
            user = await AuthService.register_student(session, reg_req, ip_address="192.168.1.100")
            await session.commit()

            # Query audit logs
            stmt = select(AuditLog).where(AuditLog.user_id == user.id)
            result = await session.execute(stmt)
            logs = result.scalars().all()
            self.assertTrue(len(logs) >= 1)
            self.assertEqual(logs[0].action, "STUDENT_REGISTER")
            self.assertEqual(logs[0].ip_address, "192.168.1.100")

    async def test_06_idor_student_profile_defense(self):
        async with self.AsyncSessionLocal() as session:
            from backend.app.schemas.user import StudentRegisterRequest
            # Register Student 1
            s1 = await AuthService.register_student(
                session,
                StudentRegisterRequest(email="student1@nexora.ai", password="PassWord#123", full_name="Student 1")
            )
            # Register Student 2
            s2 = await AuthService.register_student(
                session,
                StudentRegisterRequest(email="student2@nexora.ai", password="PassWord#123", full_name="Student 2")
            )
            await session.commit()

            # Verify that requesting s2 profile with s1 identity returns 403 Forbidden
            from backend.app.core.security import create_access_token
            s1_token = create_access_token(s1.id, UserRoleEnum.STUDENT.value)

            async with httpx.AsyncClient(transport=self.transport, base_url=self.base_url) as client:
                res = await client.get(
                    f"/api/v1/students/profile/{s2.id}",
                    headers={"Authorization": f"Bearer {s1_token}"}
                )
                self.assertEqual(res.status_code, 403)
                self.assertIn("Access forbidden", res.json()["detail"])

    async def test_07_rbac_admin_endpoint_forbidden_to_student(self):
        async with self.AsyncSessionLocal() as session:
            from backend.app.schemas.user import StudentRegisterRequest
            s = await AuthService.register_student(
                session,
                StudentRegisterRequest(email="unprivileged@nexora.ai", password="PassWord#123", full_name="Unprivileged")
            )
            await session.commit()

            from backend.app.core.security import create_access_token
            student_token = create_access_token(s.id, UserRoleEnum.STUDENT.value)

            async with httpx.AsyncClient(transport=self.transport, base_url=self.base_url) as client:
                # Student attempts to hit /api/v1/admin/users
                res = await client.get(
                    "/api/v1/admin/users",
                    headers={"Authorization": f"Bearer {student_token}"}
                )
                self.assertEqual(res.status_code, 403)
                self.assertIn("Access denied", res.json()["detail"])

if __name__ == "__main__":
    unittest.main()
