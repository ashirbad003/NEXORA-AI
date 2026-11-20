import unittest
import asyncio
import os
import uuid
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.db.session import get_db_session, Base
from backend.app.models.auth import User, Role, RefreshToken
from backend.app.schemas.user import UserRoleEnum
from backend.app.services.auth_service import AuthService
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

TEST_AUDIT_DB = "sqlite+aiosqlite:///./test_phase2_audit_sec.db"
test_engine = create_async_engine(TEST_AUDIT_DB, echo=False)
TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def override_get_db_session():
    async with TestingSessionLocal() as session:
        yield session

class TestPhase2SecurityDeepAudit(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        app.dependency_overrides[get_db_session] = override_get_db_session
        self.transport = ASGITransport(app=app)

    async def asyncTearDown(self):
        app.dependency_overrides.clear()
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await test_engine.dispose()
        if os.path.exists("./test_phase2_audit_sec.db"):
            try:
                os.remove("./test_phase2_audit_sec.db")
            except OSError:
                pass

    async def test_audit_01_token_reuse_family_revocation(self):
        """Verify that reusing an already rotated refresh token revokes all user tokens and denies access."""
        async with AsyncClient(transport=self.transport, base_url="http://testserver") as client:
            # 1. Register student
            reg_resp = await client.post("/api/v1/auth/register/student", json={
                "email": "reuse_test@nexora.ai",
                "password": "SecurePassword123!",
                "full_name": "Reuse Tester",
                "institution": "NEXORA Tech"
            })
            self.assertEqual(reg_resp.status_code, 201)

            # 2. Login
            login_resp = await client.post("/api/v1/auth/login", json={
                "email": "reuse_test@nexora.ai",
                "password": "SecurePassword123!"
            })
            self.assertEqual(login_resp.status_code, 200)
            tokens = login_resp.json()
            initial_refresh = tokens["refresh_token"]

            # 3. Legitimate refresh 1
            ref1_resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": initial_refresh})
            self.assertEqual(ref1_resp.status_code, 200)
            tokens_rot1 = ref1_resp.json()
            rotated_refresh1 = tokens_rot1["refresh_token"]
            self.assertNotEqual(initial_refresh, rotated_refresh1)

            # 4. Attacker attempts to replay initial_refresh (token reuse attack)
            replay_resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": initial_refresh})
            self.assertEqual(replay_resp.status_code, 401)
            self.assertIn("revoked", replay_resp.json()["detail"].lower())

            # 5. Verify token family revocation: even rotated_refresh1 must now be revoked
            ref2_resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": rotated_refresh1})
            self.assertEqual(ref2_resp.status_code, 401)

    async def test_audit_02_concurrent_refresh_requests(self):
        """Simulate concurrent refresh requests presenting the same refresh token."""
        async with AsyncClient(transport=self.transport, base_url="http://testserver") as client:
            await client.post("/api/v1/auth/register/student", json={
                "email": "concurrent@nexora.ai",
                "password": "SecurePassword123!",
                "full_name": "Concurrent Tester"
            })
            login_resp = await client.post("/api/v1/auth/login", json={
                "email": "concurrent@nexora.ai",
                "password": "SecurePassword123!"
            })
            refresh_token = login_resp.json()["refresh_token"]

            # Dispatch two concurrent refresh requests with identical token
            req1 = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
            req2 = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
            res1, res2 = await asyncio.gather(req1, req2)

            status_codes = [res1.status_code, res2.status_code]
            # Exactly one must succeed (200), and the other must be rejected (401)
            self.assertIn(200, status_codes, "At least one refresh request should succeed")
            self.assertIn(401, status_codes, "Duplicate concurrent refresh request must be denied")

    async def test_audit_03_deactivated_account_blocked(self):
        """Verify that a deactivated account is blocked from login and token usage."""
        async with AsyncClient(transport=self.transport, base_url="http://testserver") as client:
            reg_resp = await client.post("/api/v1/auth/register/student", json={
                "email": "deactivated@nexora.ai",
                "password": "SecurePassword123!",
                "full_name": "Deactivated User"
            })
            user_id = reg_resp.json()["id"]

            # Login once to get tokens
            login_resp = await client.post("/api/v1/auth/login", json={
                "email": "deactivated@nexora.ai",
                "password": "SecurePassword123!"
            })
            access_token = login_resp.json()["access_token"]
            refresh_token = login_resp.json()["refresh_token"]

            # Deactivate user in DB
            async with TestingSessionLocal() as session:
                user = await session.get(User, user_id)
                user.is_active = False
                await session.commit()

            # Attempt accessing /auth/me with access token -> 403 Forbidden
            me_resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})
            self.assertEqual(me_resp.status_code, 403)

            # Attempt login -> 403 Forbidden
            login_again = await client.post("/api/v1/auth/login", json={
                "email": "deactivated@nexora.ai",
                "password": "SecurePassword123!"
            })
            self.assertEqual(login_again.status_code, 403)

            # Attempt refresh -> 401 Unauthorized
            refresh_again = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
            self.assertEqual(refresh_again.status_code, 401)

    async def test_audit_04_placement_and_admin_cross_role_boundaries(self):
        """Verify role containment across Student, Placement Cell and Admin."""
        async with AsyncClient(transport=self.transport, base_url="http://testserver") as client:
            # Register student
            s_resp = await client.post("/api/v1/auth/register/student", json={
                "email": "student1@nexora.ai",
                "password": "SecurePassword123!",
                "full_name": "Student One"
            })
            s_id = s_resp.json()["id"]
            s_login = await client.post("/api/v1/auth/login", json={"email": "student1@nexora.ai", "password": "SecurePassword123!"})
            s_token = s_login.json()["access_token"]

            # Manually create placement user & admin user in DB
            async with TestingSessionLocal() as session:
                p_role = await AuthService.get_or_create_role(session, UserRoleEnum.PLACEMENT_CELL.value)
                a_role = await AuthService.get_or_create_role(session, UserRoleEnum.ADMIN.value)

                p_user = User(
                    id=str(uuid.uuid4()),
                    email="placement@nexora.ai",
                    full_name="Placement Officer",
                    hashed_password=s_resp.json()["id"], # dummy
                    is_active=True
                )
                p_user.roles.append(p_role)
                session.add(p_user)

                a_user = User(
                    id=str(uuid.uuid4()),
                    email="admin@nexora.ai",
                    full_name="Platform Admin",
                    hashed_password=s_resp.json()["id"],
                    is_active=True
                )
                a_user.roles.append(a_role)
                session.add(a_user)
                await session.commit()
                p_id = p_user.id
                a_id = a_user.id

            from backend.app.core.security import create_access_token
            p_token = create_access_token(p_id, UserRoleEnum.PLACEMENT_CELL.value)
            a_token = create_access_token(a_id, UserRoleEnum.ADMIN.value)

            # 1. Student cannot access placement list
            s_p_resp = await client.get("/api/v1/placement/students", headers={"Authorization": f"Bearer {s_token}"})
            self.assertEqual(s_p_resp.status_code, 403)

            # 2. Student cannot access admin audit logs
            s_a_resp = await client.get("/api/v1/admin/audit-logs", headers={"Authorization": f"Bearer {s_token}"})
            self.assertEqual(s_a_resp.status_code, 403)

            # 3. Placement officer CAN access placement list
            p_p_resp = await client.get("/api/v1/placement/students", headers={"Authorization": f"Bearer {p_token}"})
            self.assertEqual(p_p_resp.status_code, 200)

            # 4. Placement officer CANNOT access admin users or audit logs
            p_a_resp = await client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {p_token}"})
            self.assertEqual(p_a_resp.status_code, 403)

            # 5. Placement officer CAN access student profile (institutional oversight)
            p_s_resp = await client.get(f"/api/v1/students/profile/{s_id}", headers={"Authorization": f"Bearer {p_token}"})
            self.assertEqual(p_s_resp.status_code, 200)

            # 6. Admin CAN access all endpoints
            a_s_resp = await client.get(f"/api/v1/students/profile/{s_id}", headers={"Authorization": f"Bearer {a_token}"})
            self.assertEqual(a_s_resp.status_code, 200)
            a_u_resp = await client.get("/api/v1/admin/users", headers={"Authorization": f"Bearer {a_token}"})
            self.assertEqual(a_u_resp.status_code, 200)
            a_l_resp = await client.get("/api/v1/admin/audit-logs", headers={"Authorization": f"Bearer {a_token}"})
            self.assertEqual(a_l_resp.status_code, 200)

if __name__ == "__main__":
    unittest.main()
