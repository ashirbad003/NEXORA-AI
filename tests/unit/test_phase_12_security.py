import unittest
import asyncio
import time
from httpx import AsyncClient, ASGITransport

from backend.app.main import create_app
from backend.app.core.rate_limiter import SlidingWindowRateLimiter
from backend.app.core.telemetry import metrics, request_id_ctx

class TestPhase12SecurityAndObservability(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = create_app()
        self.transport = ASGITransport(app=self.app)

    async def test_01_http_security_headers_present(self):
        """Verify essential security headers are injected in all responses."""
        async with AsyncClient(transport=self.transport, base_url="http://test") as client:
            res = await client.get("/")
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.headers.get("X-Content-Type-Options"), "nosniff")
            self.assertEqual(res.headers.get("X-Frame-Options"), "DENY")
            self.assertEqual(res.headers.get("Referrer-Policy"), "strict-origin-when-cross-origin")
            self.assertIn("Permissions-Policy", res.headers)
            self.assertIn("X-Request-ID", res.headers)
            self.assertIn("X-Process-Time-MS", res.headers)

    async def test_02_sensitive_routes_cache_control_no_store(self):
        """Verify sensitive auth and sync endpoints forbid browser and intermediary caching."""
        async with AsyncClient(transport=self.transport, base_url="http://test") as client:
            # Login attempt without body triggers 422, but Cache-Control must still be no-store
            res = await client.post("/api/v1/auth/login", json={})
            self.assertIn("no-store", res.headers.get("Cache-Control", ""))

    async def test_03_payload_too_large_rejection(self):
        """Verify requests with Content-Length > 10MB are rejected with 413."""
        async with AsyncClient(transport=self.transport, base_url="http://test") as client:
            oversized_headers = {"Content-Length": str(15 * 1024 * 1024)}
            res = await client.post("/api/v1/auth/login", headers=oversized_headers)
            self.assertEqual(res.status_code, 413)
            self.assertEqual(res.json()["type"], "PAYLOAD_TOO_LARGE")

    async def test_04_sliding_window_rate_limiter_logic(self):
        """Verify rate limiter correctly throttles requests when limit is exceeded."""
        limiter = SlidingWindowRateLimiter(default_limit=3, default_window_seconds=2)
        key = "test_user_ip_1"

        # First 3 requests must be allowed
        a1, r1, _ = await limiter.is_allowed(key, limit=3, window_seconds=2)
        a2, r2, _ = await limiter.is_allowed(key, limit=3, window_seconds=2)
        a3, r3, _ = await limiter.is_allowed(key, limit=3, window_seconds=2)
        self.assertTrue(a1)
        self.assertTrue(a2)
        self.assertTrue(a3)
        self.assertEqual(r3, 0)

        # 4th request must be throttled
        a4, r4, retry_after = await limiter.is_allowed(key, limit=3, window_seconds=2)
        self.assertFalse(a4)
        self.assertGreaterEqual(retry_after, 1)

    async def test_05_operational_telemetry_metrics_endpoint(self):
        """Verify /metrics returns structured summary without sensitive data."""
        async with AsyncClient(transport=self.transport, base_url="http://test") as client:
            res = await client.get("/metrics")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertIn("total_requests", data)
            self.assertIn("average_latency_ms", data)
            self.assertIn("status_distribution", data)
            self.assertIn("route_distribution", data)
            self.assertIn("auth_failures", data)

    async def test_06_health_liveness_and_readiness(self):
        """Verify /health/live and /health/ready endpoints."""
        async with AsyncClient(transport=self.transport, base_url="http://test") as client:
            res_live = await client.get("/health/live")
            self.assertEqual(res_live.status_code, 200)
            self.assertEqual(res_live.json()["status"], "ok")

            res_ready = await client.get("/health/ready")
            self.assertEqual(res_ready.status_code, 200)
            ready_data = res_ready.json()
            self.assertIn(ready_data["status"], ["healthy", "degraded"])
            self.assertIn("connected", ready_data["database"])

    async def test_07_request_id_sanitization_and_length_limit(self):
        """Verify invalid or oversized client request IDs are rejected and replaced with safe UUIDs."""
        async with AsyncClient(transport=self.transport, base_url="http://test") as client:
            # Dangerous or oversized client header
            malicious_header = {"X-Request-ID": "injection_test<script>alert(1)</script>" + "A" * 100}
            res = await client.get("/", headers=malicious_header)
            self.assertEqual(res.status_code, 200)
            returned_id = res.headers.get("X-Request-ID", "")
            self.assertNotIn("<script>", returned_id)
            self.assertLessEqual(len(returned_id), 64)

    async def test_08_metrics_cardinality_ceiling(self):
        """Verify metrics collector enforces cardinality ceiling to prevent memory exhaustion."""
        from backend.app.core.telemetry import metrics
        # Record many unique routes
        for i in range(600):
            metrics.record_request("GET", f"/arbitrary/route/{i}/test", 200, 1.0)
        summary = metrics.get_summary()
        self.assertLessEqual(len(summary["route_distribution"]), 510)
        self.assertIn("OTHER_ROUTES", summary["route_distribution"])
