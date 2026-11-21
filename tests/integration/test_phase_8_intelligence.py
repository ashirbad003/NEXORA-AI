import unittest
import os
import sys
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from backend.app.db.session import Base, get_db_session
from backend.app.models.auth import User, Role, StudentProfile
from backend.app.core.security import hash_password, create_access_token
from backend.app.schemas.user import UserRoleEnum
from backend.app.main import app

TEST_DB_URL = "sqlite+aiosqlite:///./test_phase8_suite.db"

class TestPhase8ResumeGithubJob(unittest.IsolatedAsyncioTestCase):
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
        self.client = httpx.AsyncClient(transport=self.transport, base_url="http://testserver")

        self.student_id = "test-student-p8-id"
        self.admin_id = "test-admin-p8-id"

        async with self.AsyncSessionLocal() as session:
            student_role = Role(id="role-student-p8", name=UserRoleEnum.STUDENT.value)
            admin_role = Role(id="role-admin-p8", name=UserRoleEnum.ADMIN.value)
            session.add_all([student_role, admin_role])
            await session.commit()

            student_user = User(
                id=self.student_id,
                email="student@nexora.ai",
                full_name="Phase 8 Student Candidate",
                hashed_password=hash_password("StudentPass123!"),
                is_active=True,
                is_email_verified=True
            )
            student_user.roles.append(student_role)

            admin_user = User(
                id=self.admin_id,
                email="admin@nexora.ai",
                full_name="Platform Administrator",
                hashed_password=hash_password("AdminPass123!"),
                is_active=True,
                is_email_verified=True
            )
            admin_user.roles.append(admin_role)

            session.add_all([student_user, admin_user])
            await session.commit()
        self.student_token = create_access_token(subject=self.student_id, role="STUDENT")
        self.admin_token = create_access_token(subject=self.admin_id, role="ADMIN")
        self.student_headers = {"Authorization": f"Bearer {self.student_token}"}
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}

    async def asyncTearDown(self):
        await self.client.aclose()
        await self.engine.dispose()
        if os.path.exists("./test_phase8_suite.db"):
            try:
                os.remove("./test_phase8_suite.db")
            except Exception:
                pass

    async def test_01_resume_creation_ats_and_bullet_opt(self):
        payload = {
            "title": "Principal Systems Engineer Resume",
            "template_type": "Modern",
            "raw_content": "Engineered distributed Python microservices with PostgreSQL, Docker, and FastAPI. Architected scalable database queries reducing latency by 45%.",
            "structured_data": {
                "contact": {"name": "Phase 8 Candidate", "email": "student@nexora.ai", "phone": "+91 9999988888"},
                "education": ["B.Tech Computer Science"],
                "skills": ["Python", "FastAPI", "Docker", "PostgreSQL", "React"],
                "experience": ["Architected distributed systems."]
            },
            "is_primary": True
        }
        res = await self.client.post("/api/v1/resume/", json=payload, headers=self.student_headers)
        self.assertEqual(res.status_code, 201)
        data = res.json()
        resume_id = data["id"]
        self.assertEqual(data["student_id"], self.student_id)
        self.assertEqual(data["completeness_score"], 100.0)
        self.assertGreater(data["ats_score"], 40.0)

        ats_res = await self.client.get(f"/api/v1/resume/{resume_id}/ats-analysis", headers=self.student_headers)
        self.assertEqual(ats_res.status_code, 200)
        ats_data = ats_res.json()
        self.assertIn("python", ats_data["keyword_matches"])
        self.assertIn("fastapi", ats_data["keyword_matches"])

        opt_res = await self.client.post(
            "/api/v1/resume/optimize-bullet",
            json={"bullet_point": "Worked on database indexing to make it fast."},
            headers=self.student_headers
        )
        self.assertEqual(opt_res.status_code, 200)
        opt_data = opt_res.json()
        self.assertEqual(opt_data["action_verb_used"], "Architected")
        self.assertTrue(opt_data["metric_added"])


        latex_res = await self.client.get(f"/api/v1/resume/{resume_id}/export/latex", headers=self.student_headers)
        self.assertEqual(latex_res.status_code, 200)
        self.assertIn("documentclass", latex_res.text)
        self.assertIn("student@nexora.ai", latex_res.text)

    async def test_02_github_portfolio_intelligence(self):
        scan_res = await self.client.post(
            "/api/v1/github/scan",
            json={"github_username": "nexora-architect"},
            headers=self.student_headers
        )
        self.assertEqual(scan_res.status_code, 200)
        profile = scan_res.json()
        self.assertEqual(profile["github_username"], "nexora-architect")
        self.assertGreaterEqual(profile["portfolio_score"], 50.0)
        self.assertIn("Python", profile["languages_distribution"])
        self.assertTrue(len(profile["repository_health_metrics"]) >= 2)

        cached_res = await self.client.get("/api/v1/github/profile", headers=self.student_headers)
        self.assertEqual(cached_res.status_code, 200)
        self.assertEqual(cached_res.json()["github_username"], "nexora-architect")

    async def test_03_job_opportunities_kanban_and_cold_email(self):
        job_payload = {
            "company_name": "Google DeepMind",
            "role_title": "AI Systems Engineer",
            "opportunity_type": "Full-Time",
            "location": "Bengaluru / Hybrid",
            "stipend_or_salary": "INR 32 LPA",
            "description": "Architect autonomous AI pipelines.",
            "required_skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
            "is_on_campus": True
        }
        create_res = await self.client.post("/api/v1/jobs/opportunities", json=job_payload, headers=self.admin_headers)
        self.assertEqual(create_res.status_code, 201)
        job_id = create_res.json()["id"]

        list_res = await self.client.get("/api/v1/jobs/opportunities?on_campus=true", headers=self.student_headers)
        self.assertEqual(list_res.status_code, 200)
        jobs = list_res.json()
        self.assertTrue(len(jobs) >= 1)
        target_job = next(j for j in jobs if j["id"] == job_id)
        self.assertGreaterEqual(target_job["match_score"], 50.0)

        apply_res = await self.client.post(f"/api/v1/jobs/applications/{job_id}?status_state=Applied", headers=self.student_headers)
        self.assertEqual(apply_res.status_code, 201)
        application = apply_res.json()
        app_id = application["id"]
        self.assertEqual(application["status"], "Applied")

        patch_res = await self.client.patch(
            f"/api/v1/jobs/applications/{app_id}/status",
            json={"status": "Interview", "notes": "Technical rounds scheduled."},
            headers=self.student_headers
        )
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(patch_res.json()["status"], "Interview")


        email_res = await self.client.post(
            "/api/v1/jobs/cold-email",
            json={"job_id": job_id, "hiring_manager_name": "Alex Mercer"},
            headers=self.student_headers
        )
        self.assertEqual(email_res.status_code, 200)
        email_data = email_res.json()
        self.assertIn("AI Systems Engineer", email_data["subject_line"])
        self.assertIn("Alex Mercer", email_data["body_text"])
        self.assertEqual(len(email_data["tips"]), 3)

if __name__ == '__main__':
    unittest.main()
