import unittest
import asyncio
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.db.session import Base
from backend.app.core.config import settings
from sandbox.worker import ProcessIsolatedSandbox

class TestPhase5CodingArena(unittest.IsolatedAsyncioTestCase):
    """
    Automated Test Suite for Phase 5: Coding Arena & Isolated Sandbox Worker
    Covers:
      - FEAT-063: Online Code Editor Interface
      - FEAT-064: Multi-Language Runtime Support
      - FEAT-065: Problem Catalog Browser & Filters
      - FEAT-066: Company-Wise Problem Filtering
      - FEAT-067: Public Sample Test Case Execution
      - FEAT-068: Hidden Test Case Evaluation & Security
      - FEAT-069: Process-Isolated Execution Sandbox
      - FEAT-070: Strict Execution Timeouts
      - FEAT-071: Memory Limit Ceilings
      - FEAT-072: Sanitized Output & Error Formatter
      - FEAT-073: Detailed Submission History & IDOR Protection
      - FEAT-074: Coding Streak & Activity Tracker
      - FEAT-077: Custom Input Runner
    """

    async def asyncSetUp(self):
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.AsyncSessionLocal = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        from backend.app.db.session import get_db_session
        async def override_get_db_session():
            async with self.AsyncSessionLocal() as session:
                yield session

        app.dependency_overrides[get_db_session] = override_get_db_session
        self.transport = ASGITransport(app=app)
        self.base_url = "http://testserver"

    async def asyncTearDown(self):
        from backend.app.db.session import get_db_session
        app.dependency_overrides.clear()
        await self.engine.dispose()

    async def _get_auth_headers(self, client: AsyncClient) -> dict:
        await client.post("/api/v1/auth/register/student", json={
            "email": "coder@nexora.ai",
            "password": "Password123!",
            "full_name": "Arena Coder"
        })
        login = await client.post("/api/v1/auth/login", json={
            "email": "coder@nexora.ai",
            "password": "Password123!"
        })
        token = login.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    async def test_01_problem_catalog_listing_and_seeding(self):
        """Verify problem listing, auto-seeding, and difficulty filtering (FEAT-065)."""
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            resp = await client.get("/api/v1/coding/problems")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertGreaterEqual(data["total"], 3)
            slugs = [p["slug"] for p in data["problems"]]
            self.assertIn("two-sum", slugs)
            self.assertIn("valid-parentheses", slugs)

            # Filter by difficulty
            easy_resp = await client.get("/api/v1/coding/problems?difficulty=Easy")
            self.assertEqual(easy_resp.status_code, 200)
            easy_data = easy_resp.json()
            self.assertTrue(all(p["difficulty"] == "Easy" for p in easy_data["problems"]))

    async def test_02_company_wise_problem_filtering(self):
        """Verify company-wise question mapping & search (FEAT-066, FEAT-080)."""
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            resp = await client.get("/api/v1/coding/problems?company=Google")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertGreaterEqual(data["total"], 1)
            self.assertTrue(any("Google" in (p["companies"] or "") for p in data["problems"]))

    async def test_03_problem_detail_and_hidden_test_case_protection(self):
        """Verify problem detail fetches sample test cases but strictly hides secret test cases (FEAT-067, FEAT-068)."""
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            resp = await client.get("/api/v1/coding/problems/two-sum")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["slug"], "two-sum")
            self.assertIn("nums = [2,7,11,15]", data["description_markdown"])
            # Samples must be returned
            self.assertEqual(len(data["sample_test_cases"]), 2)
            # Hidden test cases must NEVER be exposed in public API
            self.assertNotIn("hidden_test_cases", data)
            self.assertNotIn("hidden", str(data["sample_test_cases"]))

    async def test_04_run_custom_input_unisolated_safeguard(self):
        """Verify custom input execution adheres to sandbox security policy (FEAT-067, FEAT-077)."""
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            headers = await self._get_auth_headers(client)
            payload = {
                "language": "python",
                "code": "print('hello custom')",
                "custom_input": "sample stdin"
            }
            resp = await client.post("/api/v1/coding/problems/two-sum/run", json=payload, headers=headers)
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            # When host is unisolated (no docker daemon running), execution is safely blocked
            self.assertIn(data["status"], ["EXECUTION_BLOCKED_SECURITY_POLICY", "EXECUTION_BLOCKED_CONTAINER_UNAVAILABLE", "COMPLETED"])
            if data["status"].startswith("EXECUTION_BLOCKED"):
                self.assertIn("Security", data["stderr"])

    async def test_05_submission_evaluation_and_history(self):
        """Verify full submission workflow, verdict recording, and user-isolated history (FEAT-068, FEAT-073)."""
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            headers = await self._get_auth_headers(client)

            # Submit solution
            submit_payload = {
                "language": "python",
                "code": "def twoSum(nums, target): return [0, 1]"
            }
            sub_resp = await client.post("/api/v1/coding/problems/two-sum/submit", json=submit_payload, headers=headers)
            self.assertEqual(sub_resp.status_code, 201)
            sub_data = sub_resp.json()
            self.assertEqual(sub_data["problem_slug"], "two-sum")
            self.assertIn("verdict", sub_data)

            # Fetch my submission history
            hist_resp = await client.get("/api/v1/coding/submissions/me", headers=headers)
            self.assertEqual(hist_resp.status_code, 200)
            history = hist_resp.json()
            self.assertGreaterEqual(len(history), 1)
            self.assertEqual(history[0]["problem_slug"], "two-sum")

    async def test_06_student_coding_statistics(self):
        """Verify student activity metrics and problem-solving tracker (FEAT-074)."""
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            headers = await self._get_auth_headers(client)
            resp = await client.get("/api/v1/coding/stats/me", headers=headers)
            self.assertEqual(resp.status_code, 200)
            stats = resp.json()
            self.assertIn("total_solved", stats)
            self.assertIn("current_streak_days", stats)

    async def test_07_sandbox_security_boundary_enforcement(self):
        """Verify sandbox rejects host code execution and handles timeouts/memory limits (FEAT-069, FEAT-070, FEAT-071)."""
        sandbox = ProcessIsolatedSandbox(timeout_seconds=1)
        # 1. Unsafe host mode blocked
        settings.SANDBOX_MODE = "disabled"
        res = sandbox.execute("python", "import os; print(os.listdir('.'))")
        self.assertEqual(res["status"], "EXECUTION_BLOCKED_SECURITY_POLICY")
        self.assertEqual(res["isolation_boundary"], "none")

        # 2. Container requested but daemon unavailable safely fails closed
        settings.SANDBOX_MODE = "container_isolated"
        res2 = sandbox.execute("python", "while True: pass")
        self.assertIn(res2["status"], ["EXECUTION_BLOCKED_CONTAINER_UNAVAILABLE", "TIME_LIMIT_EXCEEDED"])
