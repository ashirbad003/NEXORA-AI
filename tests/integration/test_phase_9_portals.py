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

TEST_DB_URL = "sqlite+aiosqlite:///./test_phase9_suite.db"

class TestPhase9PlacementAndAdmin(unittest.IsolatedAsyncioTestCase):
    """
    Integration tests covering Phase 9 (FEAT-235 to FEAT-276):
    - Module M: Placement Cell (FEAT-235..256: Campus drive lifecycle, eligibility engine, offer repository, institutional analytics)
    - Module N: Admin Intelligence (FEAT-257..276: Feature flags & kill-switches, health telemetry, diagnostic bundle generator)
    """

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

        self.student_id = "test-student-p9-id"
        self.tpo_id = "test-tpo-p9-id"
        self.admin_id = "test-admin-p9-id"

        async with self.AsyncSessionLocal() as session:
            student_role = Role(id="role-student-p9", name=UserRoleEnum.STUDENT.value)
            tpo_role = Role(id="role-tpo-p9", name=UserRoleEnum.PLACEMENT_CELL.value)
            admin_role = Role(id="role-admin-p9", name=UserRoleEnum.ADMIN.value)
            session.add_all([student_role, tpo_role, admin_role])
            await session.commit()

            student_user = User(
                id=self.student_id,
                email="student9@nexora.ai",
                full_name="Phase 9 Student",
                hashed_password=hash_password("StudentPass123!"),
                is_active=True,
                is_email_verified=True
            )
            student_user.roles.append(student_role)

            tpo_user = User(
                id=self.tpo_id,
                email="tpo@nexora.ai",
                full_name="Placement Officer",
                hashed_password=hash_password("TpoPass123!"),
                is_active=True,
                is_email_verified=True
            )
            tpo_user.roles.append(tpo_role)

            admin_user = User(
                id=self.admin_id,
                email="admin9@nexora.ai",
                full_name="Super Admin",
                hashed_password=hash_password("AdminPass123!"),
                is_active=True,
                is_email_verified=True
            )
            admin_user.roles.append(admin_role)

            profile = StudentProfile(
                user_id=self.student_id,
                department="CSE",
                batch_year=2026,
                cgpa=8.5,
                career_preferences="Distributed Systems",
                skills="Python, Docker, FastAPI"
            )

            session.add_all([student_user, tpo_user, admin_user, profile])
            await session.commit()

        self.student_token = create_access_token(self.student_id, "STUDENT")
        self.tpo_token = create_access_token(self.tpo_id, "PLACEMENT_CELL")
        self.admin_token = create_access_token(self.admin_id, "ADMIN")

        self.student_headers = {"Authorization": f"Bearer {self.student_token}"}
        self.tpo_headers = {"Authorization": f"Bearer {self.tpo_token}"}
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}"}

    async def asyncTearDown(self):
        await self.client.aclose()
        await self.engine.dispose()
        if os.path.exists("./test_phase9_suite.db"):
            try:
                os.remove("./test_phase9_suite.db")
            except Exception:
                pass

    async def test_01_placement_drive_lifecycle_and_registration(self):
        """Module M: Drive creation, student registration with automatic eligibility check (FEAT-237, FEAT-239)"""
        drive_payload = {
            "company_name": "Microsoft",
            "role_title": "Software Development Engineer",
            "ctc_lpa": 24.5,
            "tier": "Dream",
            "min_cgpa": 7.5,
            "allowed_branches": ["CSE", "IT"],
            "max_backlogs": 0,
            "description": "On-campus recruitment drive for 2026 batch."
        }
        res = await self.client.post("/api/v1/placement-cell/drives", json=drive_payload, headers=self.tpo_headers)
        self.assertEqual(res.status_code, 201)
        drive_data = res.json()
        drive_id = drive_data["id"]
        self.assertEqual(drive_data["status"], "Scheduled")

        # Student registers for drive
        reg_res = await self.client.post(f"/api/v1/placement-cell/drives/{drive_id}/register", headers=self.student_headers)
        self.assertEqual(reg_res.status_code, 201)
        reg_data = reg_res.json()
        self.assertEqual(reg_data["status"], "Approved")
        self.assertTrue(reg_data["is_eligible"])

        # TPO updates status to Shortlisted with interview slot (FEAT-241, FEAT-250)
        reg_id = reg_data["id"]
        patch_res = await self.client.patch(
            f"/api/v1/placement-cell/registrations/{reg_id}",
            json={"status": "Shortlisted", "interview_slot": "Panel A - 10:30 AM"},
            headers=self.tpo_headers
        )
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(patch_res.json()["interview_slot"], "Panel A - 10:30 AM")

    async def test_02_placement_offers_and_institutional_analytics(self):
        """Module M: Offer letter issuance, student offer tracking, institutional KPIs (FEAT-235, FEAT-242)"""
        # Create drive first
        drive_res = await self.client.post(
            "/api/v1/placement-cell/drives",
            json={
                "company_name": "Amazon",
                "role_title": "Cloud Architect",
                "ctc_lpa": 28.0,
                "tier": "Super-Dream",
                "min_cgpa": 8.0,
                "allowed_branches": ["CSE"],
                "max_backlogs": 0,
                "description": "Cloud architecture drive."
            },
            headers=self.tpo_headers
        )
        drive_id = drive_res.json()["id"]

        # Extend offer
        offer_payload = {
            "drive_id": drive_id,
            "student_id": self.student_id,
            "company_name": "Amazon",
            "designation": "Cloud Architect",
            "ctc_lpa": 28.0,
            "offer_letter_url": "https://storage.nexora.ai/offers/amazon-student9.pdf"
        }
        offer_res = await self.client.post("/api/v1/placement-cell/offers", json=offer_payload, headers=self.tpo_headers)
        self.assertEqual(offer_res.status_code, 201)
        offer_data = offer_res.json()
        self.assertEqual(offer_data["status"], "Offered")
        self.assertEqual(offer_data["ctc_lpa"], 28.0)

        # Institutional Analytics
        stats_res = await self.client.get("/api/v1/placement-cell/analytics/institutional", headers=self.tpo_headers)
        self.assertEqual(stats_res.status_code, 200)
        stats = stats_res.json()
        self.assertGreaterEqual(stats["total_offers_extended"], 1)
        self.assertGreaterEqual(stats["highest_ctc_lpa"], 28.0)
        self.assertIn("CSE", stats["branch_wise_stats"])

    async def test_03_admin_feature_flags_and_diagnostics(self):
        """Module N: Feature flags management, telemetry endpoint, diagnostic bundle (FEAT-262, FEAT-272, FEAT-276)"""
        # List flags
        flags_res = await self.client.get("/api/v1/admin-intelligence/flags", headers=self.admin_headers)
        self.assertEqual(flags_res.status_code, 200)
        flags = flags_res.json()
        self.assertTrue(len(flags) >= 4)

        # Toggle flag
        update_res = await self.client.post(
            "/api/v1/admin-intelligence/flags",
            json={"flag_key": "FEAT_SANDBOX_DOCKER", "is_enabled": False},
            headers=self.admin_headers
        )
        self.assertEqual(update_res.status_code, 200)
        self.assertFalse(update_res.json()["is_enabled"])

        # Health telemetry
        telemetry_res = await self.client.get("/api/v1/admin-intelligence/telemetry", headers=self.admin_headers)
        self.assertEqual(telemetry_res.status_code, 200)
        telem = telemetry_res.json()
        self.assertEqual(telem["status"], "HEALTHY")
        self.assertTrue(telem["database_connected"])

        # Diagnostic bundle generator
        diag_res = await self.client.post("/api/v1/admin-intelligence/diagnostics/generate", headers=self.admin_headers)
        self.assertEqual(diag_res.status_code, 200)
        diag = diag_res.json()
        self.assertTrue(diag["healthy"])
        self.assertEqual(diag["checks"]["postgres_connection"], "PASS")

if __name__ == "__main__":
    unittest.main()
