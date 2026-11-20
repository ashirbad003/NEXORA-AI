import unittest
import os
import sys
import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.app.db.session import Base, get_db_session
from backend.app.models.auth import User, Role, StudentProfile
from backend.app.core.security import hash_password
from backend.app.schemas.user import UserRoleEnum
from backend.app.main import app

TEST_DB_URL = "sqlite+aiosqlite:///./test_phase3_suite.db"

class TestPhase3CoreAPIs(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine(TEST_DB_URL, echo=False)
        self.AsyncSessionLocal = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

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

        # Pre-seed basic roles
        async with self.AsyncSessionLocal() as session:
            for r_name in [UserRoleEnum.STUDENT.value, UserRoleEnum.ADMIN.value, UserRoleEnum.PLACEMENT_CELL.value]:
                role = Role(id=f"role_{r_name.lower()}", name=r_name, description=f"{r_name} role")
                session.add(role)
            await session.commit()

    async def asyncTearDown(self):
        app.dependency_overrides.clear()
        await self.engine.dispose()
        if os.path.exists("./test_phase3_suite.db"):
            try:
                os.remove("./test_phase3_suite.db")
            except Exception:
                pass

    async def test_01_student_profile_update_and_readiness_calculation(self):
        async with httpx.AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            # Register student
            reg_res = await client.post("/api/v1/auth/register/student", json={
                "email": "student_p3@test.com",
                "password": "Password123!",
                "full_name": "Test Student P3",
                "institution": "MIT",
                "department": "CSE",
                "batch_year": 2026
            })
            self.assertEqual(reg_res.status_code, 201)

            # Login as student to get token
            login_res = await client.post("/api/v1/auth/login", json={
                "email": "student_p3@test.com",
                "password": "Password123!"
            })
            self.assertEqual(login_res.status_code, 200)
            token = login_res.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # Fetch initial profile (initial readiness score default is 0)
            prof_res = await client.get("/api/v1/students/my-profile", headers=headers)
            self.assertEqual(prof_res.status_code, 200)
            self.assertEqual(prof_res.json()["institution"], "MIT")
            self.assertEqual(prof_res.json()["readiness_score"], 0)

            # Update profile
            update_res = await client.put("/api/v1/students/my-profile", headers=headers, json={
                "cgpa": 9.5,
                "skills": "Python, TypeScript, SQL, Docker",
                "career_preferences": "Backend Engineer / AI Architect"
            })
            self.assertEqual(update_res.status_code, 200)
            data = update_res.json()
            self.assertEqual(data["cgpa"], 9.5)
            self.assertIn("Python", data["skills"])
            self.assertGreaterEqual(data["readiness_score"], 90)

    async def test_02_placement_cell_cohort_filters(self):
        async with httpx.AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            # Register two students
            s1 = await client.post("/api/v1/auth/register/student", json={
                "email": "alice_p3@test.com",
                "password": "Password123!",
                "full_name": "Alice P3",
                "department": "CSE",
                "batch_year": 2026
            })
            self.assertEqual(s1.status_code, 201)
            l1 = await client.post("/api/v1/auth/login", json={"email": "alice_p3@test.com", "password": "Password123!"})
            t1 = l1.json()["access_token"]
            await client.put("/api/v1/students/my-profile", headers={"Authorization": f"Bearer {t1}"}, json={
                "cgpa": 8.8,
                "skills": "Python, FastAPI"
            })

            s2 = await client.post("/api/v1/auth/register/student", json={
                "email": "bob_p3@test.com",
                "password": "Password123!",
                "full_name": "Bob P3",
                "department": "ECE",
                "batch_year": 2025
            })
            self.assertEqual(s2.status_code, 201)
            l2 = await client.post("/api/v1/auth/login", json={"email": "bob_p3@test.com", "password": "Password123!"})
            t2 = l2.json()["access_token"]
            await client.put("/api/v1/students/my-profile", headers={"Authorization": f"Bearer {t2}"}, json={
                "cgpa": 7.2,
                "skills": "C, Embedded"
            })

            # Create placement cell user directly in DB
            async with self.AsyncSessionLocal() as session:
                placement_role = await session.get(Role, "role_placement_cell")
                plc_user = User(
                    id="plc_001",
                    email="plc_p3@test.com",
                    full_name="Placement Officer",
                    hashed_password=hash_password("Password123!"),
                    is_active=True
                )
                plc_user.roles.append(placement_role)
                session.add(plc_user)
                await session.commit()

            # Login as placement cell
            login_res = await client.post("/api/v1/auth/login", json={
                "email": "plc_p3@test.com",
                "password": "Password123!"
            })
            self.assertEqual(login_res.status_code, 200)
            plc_token = login_res.json()["access_token"]
            plc_headers = {"Authorization": f"Bearer {plc_token}"}

            # Query filtered by department CSE
            cse_res = await client.get("/api/v1/placement/students?department=CSE", headers=plc_headers)
            self.assertEqual(cse_res.status_code, 200)
            self.assertEqual(len(cse_res.json()), 1)
            self.assertEqual(cse_res.json()[0]["department"], "CSE")

            # Query filtered by min_cgpa 8.0
            cgpa_res = await client.get("/api/v1/placement/students?min_cgpa=8.0", headers=plc_headers)
            self.assertEqual(cgpa_res.status_code, 200)
            self.assertEqual(len(cgpa_res.json()), 1)
            self.assertGreaterEqual(cgpa_res.json()[0]["cgpa"], 8.0)

    async def test_03_admin_paginated_users_and_audit_logs(self):
        async with httpx.AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            # Create admin user
            async with self.AsyncSessionLocal() as session:
                admin_role = await session.get(Role, "role_admin")
                admin_user = User(
                    id="admin_001",
                    email="admin_p3@test.com",
                    full_name="Super Admin",
                    hashed_password=hash_password("Password123!"),
                    is_active=True
                )
                admin_user.roles.append(admin_role)
                session.add(admin_user)
                await session.commit()

            login_res = await client.post("/api/v1/auth/login", json={
                "email": "admin_p3@test.com",
                "password": "Password123!"
            })
            self.assertEqual(login_res.status_code, 200)
            admin_token = login_res.json()["access_token"]
            admin_headers = {"Authorization": f"Bearer {admin_token}"}

            users_res = await client.get("/api/v1/admin/users?limit=10&skip=0", headers=admin_headers)
            self.assertEqual(users_res.status_code, 200)
            self.assertGreaterEqual(len(users_res.json()), 1)

            audit_res = await client.get("/api/v1/admin/audit-logs?limit=5", headers=admin_headers)
            self.assertEqual(audit_res.status_code, 200)
            self.assertIsInstance(audit_res.json(), list)
