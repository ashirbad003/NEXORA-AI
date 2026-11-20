import os
import unittest
import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport

from backend.app.core.config import settings
from backend.app.models.auth import Base, User, StudentProfile, Role, RefreshToken
from backend.app.schemas.user import UserRoleEnum
from backend.app.services.auth_service import AuthService
from backend.app.main import app
from backend.app.db.session import get_db_session

# Load TEST_DATABASE_URL from environment or backend/.env settings
PG_TEST_URL = os.environ.get("TEST_DATABASE_URL") or getattr(settings, "TEST_DATABASE_URL", "")
if not PG_TEST_URL:
    try:
        from dotenv import dotenv_values
        from pathlib import Path
        env_dict = dotenv_values(Path(__file__).resolve().parent.parent.parent / "backend" / ".env")
        PG_TEST_URL = env_dict.get("TEST_DATABASE_URL", "")
    except Exception:
        pass

IS_POSTGRES_CONFIGURED = PG_TEST_URL.startswith("postgresql+asyncpg://")

@unittest.skipUnless(IS_POSTGRES_CONFIGURED, "PostgreSQL test database credentials (TEST_DATABASE_URL) not configured in environment")
class TestPostgreSQLIntegrationLive(unittest.IsolatedAsyncioTestCase):
    """
    Live PostgreSQL 17 Integration Test Suite
    Tests run strictly against dedicated PostgreSQL test instance (nexora_test).
    Targeting development or production databases (nexora_dev) is prohibited.
    """

    async def asyncSetUp(self):
        if not IS_POSTGRES_CONFIGURED or "nexora_dev" in PG_TEST_URL:
            self.skipTest("Safety Halt: TEST_DATABASE_URL must target nexora_test, never nexora_dev.")
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
        self.engine = create_async_engine(PG_TEST_URL, echo=False)
        self.SessionLocal = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

        # Ensure clean schema in the dedicated test database (nexora_test only)
        from sqlalchemy import text
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            # Truncate tables between tests in nexora_test to ensure isolation
            await conn.execute(text(
                "TRUNCATE TABLE audit_logs, refresh_tokens, student_profiles, "
                "placement_cell_profiles, admin_profiles, user_roles, users, roles CASCADE;"
            ))

        async def override_get_db_session():
            async with self.SessionLocal() as session:
                yield session

        app.dependency_overrides[get_db_session] = override_get_db_session
        self.transport = ASGITransport(app=app)

    async def asyncTearDown(self):
        app.dependency_overrides.clear()
        if hasattr(self, "engine"):
            await self.engine.dispose()

    async def test_pg_01_registration_and_argon2_storage(self):
        """Verify user registration, Argon2id hash storage, and student profile in PostgreSQL."""
        async with AsyncClient(transport=self.transport, base_url="http://testserver") as client:
            resp = await client.post("/api/v1/auth/register/student", json={
                "email": "pg_student@nexora.ai",
                "password": "SecurePassword123!",
                "full_name": "PG Student",
                "institution": "Postgres Tech Institute"
            })
            self.assertEqual(resp.status_code, 201)
            data = resp.json()
            self.assertEqual(data["email"], "pg_student@nexora.ai")
            self.assertEqual(data["roles"][0]["name"], "STUDENT")

            # Verify in PostgreSQL
            async with self.SessionLocal() as session:
                user = await session.get(User, data["id"])
                self.assertIsNotNone(user)
                self.assertTrue(user.hashed_password.startswith("$argon2id$"))

    async def test_pg_02_duplicate_email_rejection(self):
        """Verify PostgreSQL unique constraint enforcement on users.email."""
        async with AsyncClient(transport=self.transport, base_url="http://testserver") as client:
            await client.post("/api/v1/auth/register/student", json={
                "email": "pg_dup@nexora.ai",
                "password": "SecurePassword123!",
                "full_name": "Original"
            })
            dup_resp = await client.post("/api/v1/auth/register/student", json={
                "email": "pg_dup@nexora.ai",
                "password": "SecurePassword123!",
                "full_name": "Duplicate"
            })
            self.assertEqual(dup_resp.status_code, 409)

    async def test_pg_03_login_and_token_rotation(self):
        """Verify JWT login, token refresh rotation, and revocation on PostgreSQL."""
        async with AsyncClient(transport=self.transport, base_url="http://testserver") as client:
            await client.post("/api/v1/auth/register/student", json={
                "email": "pg_login@nexora.ai",
                "password": "SecurePassword123!",
                "full_name": "Login Tester"
            })
            login_resp = await client.post("/api/v1/auth/login", json={
                "email": "pg_login@nexora.ai",
                "password": "SecurePassword123!"
            })
            self.assertEqual(login_resp.status_code, 200)
            tokens = login_resp.json()
            old_refresh = tokens["refresh_token"]

            # Refresh
            ref_resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
            self.assertEqual(ref_resp.status_code, 200)
            new_tokens = ref_resp.json()
            self.assertNotEqual(old_refresh, new_tokens["refresh_token"])

            # Old token must now be revoked
            old_ref_resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
            self.assertEqual(old_ref_resp.status_code, 401)

    async def test_pg_04_atomic_refresh_concurrency(self):
        """Verify that concurrent refresh requests on PostgreSQL permit exactly one token pair."""
        async with AsyncClient(transport=self.transport, base_url="http://testserver") as client:
            await client.post("/api/v1/auth/register/student", json={
                "email": "pg_conc@nexora.ai",
                "password": "SecurePassword123!",
                "full_name": "Conc Tester"
            })
            login_resp = await client.post("/api/v1/auth/login", json={
                "email": "pg_conc@nexora.ai",
                "password": "SecurePassword123!"
            })
            refresh_token = login_resp.json()["refresh_token"]

            req1 = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
            req2 = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
            r1, r2 = await asyncio.gather(req1, req2)

            codes = [r1.status_code, r2.status_code]
            self.assertIn(200, codes)
            self.assertIn(401, codes)

    async def test_pg_05_idor_protection(self):
        """Verify query-level IDOR scoping on PostgreSQL."""
        async with AsyncClient(transport=self.transport, base_url="http://testserver") as client:
            s1 = await client.post("/api/v1/auth/register/student", json={
                "email": "pg_s1@nexora.ai", "password": "Password123!", "full_name": "Student 1"
            })
            s2 = await client.post("/api/v1/auth/register/student", json={
                "email": "pg_s2@nexora.ai", "password": "Password123!", "full_name": "Student 2"
            })
            s1_id = s1.json()["id"]
            s2_id = s2.json()["id"]

            l1 = await client.post("/api/v1/auth/login", json={"email": "pg_s1@nexora.ai", "password": "Password123!"})
            t1 = l1.json()["access_token"]

            # Own profile
            p1 = await client.get(f"/api/v1/students/profile/{s1_id}", headers={"Authorization": f"Bearer {t1}"})
            self.assertEqual(p1.status_code, 200)

            # Other student profile
            p2 = await client.get(f"/api/v1/students/profile/{s2_id}", headers={"Authorization": f"Bearer {t1}"})
            self.assertEqual(p2.status_code, 403)

if __name__ == "__main__":
    unittest.main()
