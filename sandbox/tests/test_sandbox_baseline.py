import unittest
from sandbox.worker import ProcessIsolatedSandbox
from backend.app.core.config import settings

class TestSandboxSecurityBoundary(unittest.TestCase):
    def setUp(self):
        self.sandbox = ProcessIsolatedSandbox(timeout_seconds=2)

    def test_arbitrary_code_blocked_when_unisolated(self):
        """Verify that untrusted code execution is blocked when no container boundary is active."""
        settings.SANDBOX_MODE = "disabled"
        res = self.sandbox.execute_python("print('malicious code')")
        self.assertEqual(res["status"], "EXECUTION_BLOCKED_SECURITY_POLICY")
        self.assertIn("Security Policy: Arbitrary code execution is disabled", res["stderr"])
        self.assertEqual(res["isolation_boundary"], "none")

    def test_subprocess_host_fallback_prohibited(self):
        """Verify that mode cannot silently fall back to host subprocess execution."""
        settings.SANDBOX_MODE = "subprocess_unsafe"
        res = self.sandbox.execute_python("import os; os.system('calc.exe')")
        self.assertEqual(res["status"], "EXECUTION_BLOCKED_SECURITY_POLICY")
        self.assertIn("Security Policy", res["stderr"])

if __name__ == "__main__":
    unittest.main()
