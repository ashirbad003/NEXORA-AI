import unittest
import os
import sys
import httpx
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.main import app

class TestBackendLiveEndpoints(unittest.TestCase):
    def setUp(self):
        self.transport = httpx.ASGITransport(app=app)

    def test_root_endpoint(self):
        async def run():
            async with httpx.AsyncClient(transport=self.transport, base_url="http://testserver") as client:
                res = await client.get("/")
                self.assertEqual(res.status_code, 200)
                data = res.json()
                self.assertEqual(data["name"], "NEXORA AI")
                self.assertIn("version", data)
        asyncio.run(run())

    def test_health_live_endpoint(self):
        async def run():
            async with httpx.AsyncClient(transport=self.transport, base_url="http://testserver") as client:
                res = await client.get("/health/live")
                self.assertEqual(res.status_code, 200)
                self.assertEqual(res.json()["status"], "ok")
        asyncio.run(run())

    def test_health_ready_endpoint(self):
        async def run():
            async with httpx.AsyncClient(transport=self.transport, base_url="http://testserver") as client:
                res = await client.get("/health/ready")
                self.assertEqual(res.status_code, 200)
                data = res.json()
                self.assertEqual(data["status"], "healthy")
                self.assertIn("environment", data)
                self.assertIn("database", data)
                self.assertIn("ai_engine", data)
                self.assertIn("sandbox", data)
        asyncio.run(run())

if __name__ == "__main__":
    unittest.main()
