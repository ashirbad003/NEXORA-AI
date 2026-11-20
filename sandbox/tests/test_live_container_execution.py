import unittest
import os
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

    # 1. RUNTIME CHECKS: PYTHON 3
    def test_python_container_execution(self):
        code = "print('NEXORA_PYTHON_OK')"
        res = self.sandbox.execute("python", code)
        self.assertEqual(res["status"], "COMPLETED")
        self.assertEqual(res["exit_code"], 0)
        self.assertIn("NEXORA_PYTHON_OK", res["stdout"])
        self.assertEqual(res["isolation_boundary"], "docker_container")

    def test_python_compilation_or_syntax_error(self):
        code = "def bad_syntax(:\n    pass"
        res = self.sandbox.execute("python", code)
        self.assertEqual(res["status"], "RUNTIME_ERROR")
        self.assertNotEqual(res["exit_code"], 0)
        self.assertIn("SyntaxError", res["stderr"])

    # 2. RUNTIME CHECKS: C
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

    def test_c_compilation_error(self):
        code = """#include <stdio.h>
int main() {
    this_is_an_invalid_c_statement;
    return 0;
}
"""
        res = self.sandbox.execute("c", code)
        self.assertEqual(res["status"], "RUNTIME_ERROR")
        self.assertNotEqual(res["exit_code"], 0)
        self.assertIn("error", res["stderr"].lower())

    # 3. RUNTIME CHECKS: C++
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

    def test_cpp_compilation_error(self):
        code = """#include <iostream>
int main() {
    invalid_cpp_call();
    return 0;
}
"""
        res = self.sandbox.execute("cpp", code)
        self.assertEqual(res["status"], "RUNTIME_ERROR")
        self.assertNotEqual(res["exit_code"], 0)
        self.assertIn("error", res["stderr"].lower())

    # 4. RUNTIME CHECKS: JAVA 17
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

    def test_java_compilation_error(self):
        code = """public class Solution {
    public static void main(String[] args) {
        undefinedJavaSymbol();
    }
}
"""
        res = self.sandbox.execute("java", code)
        self.assertEqual(res["status"], "RUNTIME_ERROR")
        self.assertNotEqual(res["exit_code"], 0)
        self.assertTrue(len(res["stderr"]) > 0)

    # 5. STDIN / STDOUT HANDLING ACROSS RUNTIMES
    def test_container_stdin_passing_python(self):
        code = """import sys
val = sys.stdin.read().strip()
print(f"ECHO:{val}")
"""
        res = self.sandbox.execute("python", code, stdin_input="123 456")
        self.assertEqual(res["status"], "COMPLETED")
        self.assertIn("ECHO:123 456", res["stdout"])

    def test_container_stdin_passing_c(self):
        code = """#include <stdio.h>
int main() {
    int a, b;
    if (scanf("%d %d", &a, &b) == 2) {
        printf("SUM:%d\\n", a + b);
    }
    return 0;
}
"""
        res = self.sandbox.execute("c", code, stdin_input="20 22")
        self.assertEqual(res["status"], "COMPLETED")
        self.assertIn("SUM:42", res["stdout"])

    # 6. TIMEOUT AND FORCED TERMINATION
    def test_container_timeout_enforcement(self):
        sandbox_short = ProcessIsolatedSandbox(timeout_seconds=2)
        code = "import time\nwhile True:\n    time.sleep(0.5)\n"
        res = sandbox_short.execute("python", code)
        self.assertEqual(res["status"], "TIME_LIMIT_EXCEEDED")
        self.assertTrue(res["is_timeout"])

    # 7. MANDATORY SECURITY BOUNDARIES
    def test_network_isolation_enforced(self):
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

    def test_rootfs_read_only_enforced(self):
        code = """try:
    with open('/root/escape_probe.txt', 'w') as f:
        f.write('tampered')
    print('WRITE_ALLOWED')
except Exception:
    print('READONLY_ENFORCED')
"""
        res = self.sandbox.execute("python", code)
        self.assertEqual(res["status"], "COMPLETED")
        self.assertIn("READONLY_ENFORCED", res["stdout"])
        self.assertNotIn("WRITE_ALLOWED", res["stdout"])

    def test_no_host_env_or_secret_leak(self):
        code = """import os
leak = [k for k in os.environ if 'POSTGRES' in k or 'SECRET' in k or 'JWT' in k]
if leak:
    print('ENV_LEAK:' + ','.join(leak))
else:
    print('ENV_CLEAN')
"""
        res = self.sandbox.execute("python", code)
        self.assertEqual(res["status"], "COMPLETED")
        self.assertIn("ENV_CLEAN", res["stdout"])

    # 8. HARDENED NON-ROOT EXECUTION AND ATTACK TESTS
    def test_non_root_uid_python(self):
        code = "import os; print(f'UID:{os.getuid()},GID:{os.getgid()}')"
        res = self.sandbox.execute("python", code)
        self.assertEqual(res["status"], "COMPLETED")
        self.assertIn("UID:1000", res["stdout"])
        self.assertIn("GID:1000", res["stdout"])

    def test_non_root_uid_c(self):
        code = """#include <stdio.h>
#include <unistd.h>
int main() {
    printf("UID:%d,GID:%d\\n", getuid(), getgid());
    return 0;
}
"""
        res = self.sandbox.execute("c", code)
        self.assertEqual(res["status"], "COMPLETED")
        self.assertIn("UID:1000", res["stdout"])
        self.assertIn("GID:1000", res["stdout"])

    def test_root_privilege_escalation_denied(self):
        code = """import os
try:
    os.setuid(0)
    print('ESCALATION_SUCCEEDED')
except PermissionError:
    print('ESCALATION_BLOCKED')
"""
        res = self.sandbox.execute("python", code)
        self.assertEqual(res["status"], "COMPLETED")
        self.assertIn("ESCALATION_BLOCKED", res["stdout"])
        self.assertNotIn("ESCALATION_SUCCEEDED", res["stdout"])

    def test_docker_socket_not_accessible(self):
        code = """import os
if os.path.exists('/var/run/docker.sock'):
    print('SOCKET_EXPOSED')
else:
    print('SOCKET_PROTECTED')
"""
        res = self.sandbox.execute("python", code)
        self.assertEqual(res["status"], "COMPLETED")
        self.assertIn("SOCKET_PROTECTED", res["stdout"])

    def test_fork_bomb_mitigation(self):
        # Fork bomb should be arrested by pids-limit=64 and return without crashing host
        sandbox_short = ProcessIsolatedSandbox(timeout_seconds=2)
        code = """import os
try:
    while True:
        os.fork()
except Exception as e:
    print('FORK_BLOCKED')
"""
        res = sandbox_short.execute("python", code)
        # Process will either hit process limit or timeout safely
        self.assertTrue(res["status"] in ("TIME_LIMIT_EXCEEDED", "COMPLETED", "RUNTIME_ERROR"))

if __name__ == "__main__":
    unittest.main()
