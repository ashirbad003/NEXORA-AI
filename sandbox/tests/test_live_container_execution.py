import unittest
from sandbox.worker import ProcessIsolatedSandbox
from backend.app.core.config import settings

class TestLiveContainerExecution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sandbox = ProcessIsolatedSandbox(timeout_seconds=5)
        cls.orig_mode = settings.SANDBOX_MODE
        settings.SANDBOX_MODE = "container_isolated"

    @classmethod
    def tearDownClass(cls):
        settings.SANDBOX_MODE = cls.orig_mode

    def test_python_container_execution(self):
        code = "print('NEXORA_PYTHON_OK')"
        res = self.sandbox.execute("python", code)
        self.assertEqual(res["status"], "COMPLETED")
        self.assertEqual(res["exit_code"], 0)
        self.assertIn("NEXORA_PYTHON_OK", res["stdout"])
        self.assertEqual(res["isolation_boundary"], "docker_container")

    def test_c_container_execution(self):
        code = """#include <stdio.h>
int main() {
    printf("NEXORA_C_OK\\n");
    return 0;
}
"""
        res = self.sandbox.execute("c", code)
        self.assertEqual(res["status"], "COMPLETED")
        self.assertEqual(res["exit_code"], 0)
        self.assertIn("NEXORA_C_OK", res["stdout"])
        self.assertEqual(res["isolation_boundary"], "docker_container")

    def test_cpp_container_execution(self):
        code = """#include <iostream>
int main() {
    std::cout << "NEXORA_CPP_OK" << std::endl;
    return 0;
}
"""
        res = self.sandbox.execute("cpp", code)
        self.assertEqual(res["status"], "COMPLETED")
        self.assertEqual(res["exit_code"], 0)
        self.assertIn("NEXORA_CPP_OK", res["stdout"])
        self.assertEqual(res["isolation_boundary"], "docker_container")

    def test_java_container_execution(self):
        code = """public class Solution {
    public static void main(String[] args) {
        System.out.println("NEXORA_JAVA_OK");
    }
}
"""
        res = self.sandbox.execute("java", code)
        self.assertEqual(res["status"], "COMPLETED")
        self.assertEqual(res["exit_code"], 0)
        self.assertIn("NEXORA_JAVA_OK", res["stdout"])
        self.assertEqual(res["isolation_boundary"], "docker_container")

    def test_container_stdin_passing(self):
        code = """import sys
val = sys.stdin.read().strip()
print(f"ECHO:{val}")
"""
        res = self.sandbox.execute("python", code, stdin_input="123 456")
        self.assertEqual(res["status"], "COMPLETED")
        self.assertIn("ECHO:123 456", res["stdout"])

    def test_container_timeout_enforcement(self):
        sandbox_short = ProcessIsolatedSandbox(timeout_seconds=2)
        code = "import time\nwhile True:\n    time.sleep(0.5)\n"
        res = sandbox_short.execute("python", code)
        self.assertEqual(res["status"], "TIME_LIMIT_EXCEEDED")
        self.assertTrue(res["is_timeout"])

    def test_network_isolation_enforced(self):
        # Attempting outbound socket must fail closed with error
        code = """import urllib.request
try:
    urllib.request.urlopen('http://1.1.1.1', timeout=1)
    print('NET_LEAK')
except Exception as e:
    print('NET_BLOCKED')
"""
        res = self.sandbox.execute("python", code)
        self.assertEqual(res["status"], "COMPLETED")
        self.assertIn("NET_BLOCKED", res["stdout"])
        self.assertNotIn("NET_LEAK", res["stdout"])

if __name__ == "__main__":
    unittest.main()
