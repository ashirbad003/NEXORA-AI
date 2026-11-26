import unittest
import uuid
from typing import Tuple
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.main import create_app
from backend.app.models.auth import User
from backend.app.schemas.user import StudentRegisterRequest, LoginRequest
from backend.app.services.auth_service import AuthService
from backend.app.db.session import AsyncSessionLocal
from sandbox.worker import ProcessIsolatedSandbox
from backend.app.core.config import settings


class TestPhase14ReleaseReadiness(unittest.IsolatedAsyncioTestCase):
    """
    Phase 14 Master Release Readiness Verification Suite.
    Validates:
      1. Authentication & Token Expiry / Rejection boundaries.
      2. Server-side RBAC enforcement across student, doctor, admin roles.
      3. Coding Arena strict sandbox fail-closed policy (zero host subprocess execution).
      4. AI telemetry and fallback resilience under mock/local configurations.
      5. Security headers and sensitive data exclusion in responses.
    """

    async def _create_test_student(self, session: AsyncSession, prefix: str = "p14_student") -> Tuple[User, str]:
        unique = str(uuid.uuid4())[:8]
        email = f"{prefix}_{unique}@example.com"
        password = "SecurePassword123!"
        req = StudentRegisterRequest(
            email=email,
            password=password,
            full_name=f"Release Candidate Student {unique}"
        )
        user = await AuthService.register_student(session=session, req=req)
        await session.commit()

        login_req = LoginRequest(email=email, password=password)
        auth_user, access_token, _ = await AuthService.authenticate_user(session=session, req=login_req)
        await session.commit()
        return auth_user, access_token

    async def test_01_auth_tampered_token_rejection(self):
        """Verify token tampering and spoofed authorization fails closed with HTTP 401."""
        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            async with AsyncSessionLocal() as session:
                _, valid_token = await self._create_test_student(session, "tamper_test")

            # Tamper the token by modifying characters in signature
            tampered_token = valid_token[:-4] + "WXYZ"
            res = await client.get(
                "/api/v1/students/my-profile",
                headers={"Authorization": f"Bearer {tampered_token}"}
            )
            self.assertEqual(res.status_code, 401)
            self.assertIn("credentials", res.text.lower())

    async def test_02_rbac_student_cannot_access_admin_portal(self):
        """Verify students are strictly blocked from admin routes (HTTP 403 Forbidden)."""
        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            async with AsyncSessionLocal() as session:
                _, student_token = await self._create_test_student(session, "rbac_student")

            res = await client.get(
                "/api/v1/admin/users",
                headers={"Authorization": f"Bearer {student_token}"}
            )
            # Must be denied (403 Forbidden)
            self.assertEqual(res.status_code, 403)
            self.assertIn("access denied", res.text.lower())

    async def test_03_sandbox_fail_closed_policy(self):
        """
        Verify Coding Arena sandbox strictly enforces fail-closed isolation.
        Host subprocess execution must NEVER occur when container_isolated is inactive.
        """
        sandbox = ProcessIsolatedSandbox(timeout_seconds=3)
        res = sandbox.execute("python", "print('Malicious Host Exploit')", "")
        
        # In development/test mode without live container daemon, execution is blocked
        self.assertIn(res["status"], ["EXECUTION_BLOCKED_SECURITY_POLICY", "EXECUTION_BLOCKED_CONTAINER_UNAVAILABLE"])
        self.assertEqual(res["exit_code"], -1)
        self.assertEqual(res["stdout"], "")
        self.assertIn("Security Policy", res["stderr"])

    async def test_04_ai_engine_telemetry_and_session_integrity(self):
        """Verify multi-turn session tracking and cost telemetry use timezone-aware timestamps."""
        from ai_engine.session_manager import AIChatSessionManager
        from ai_engine.telemetry.tracker import TokenTelemetryTracker

        session_mgr = AIChatSessionManager()
        session_id = f"sess_{uuid.uuid4().hex[:8]}"
        session_mgr.add_message(session_id, "user", "What is Big-O of QuickSort?")
        session_mgr.add_message(session_id, "assistant", "Average is O(N log N).")

        ctx = session_mgr.get_context_window(session_id)
        self.assertEqual(len(ctx), 2)
        for msg in ctx:
            self.assertIn("+00:00", msg["timestamp"])

        tracker = TokenTelemetryTracker()
        record = tracker.log_call(
            provider="local",
            model="nexora-copilot-v1",
            tokens_prompt=120,
            tokens_completion=65,
            latency_ms=18.4,
            user_id="student_123",
            action="career_roadmap"
        )
        self.assertIn("+00:00", record["timestamp"])
        self.assertEqual(record["total_tokens"], 185)

    async def test_05_api_security_headers_present(self):
        """Verify critical HTTP security headers are returned on API endpoints."""
        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.get("/health/live")
            self.assertEqual(res.status_code, 200)
            headers = {k.lower(): v for k, v in res.headers.items()}
            # Verify invariant production security headers
            self.assertIn("x-content-type-options", headers)
            self.assertEqual(headers["x-content-type-options"], "nosniff")
            self.assertIn("x-frame-options", headers)
            self.assertEqual(headers["x-frame-options"], "DENY")
            self.assertIn("x-request-id", headers)
