# NEXORA AI: Coding Sandbox Threat Model & Isolation Architecture

**Auditor:** Principal Cybersecurity & Sandbox Isolation Architect  
**Inspection Target:** `sandbox/worker.py`, `sandbox/tests/`  
**Date:** November 19, 2026  

---

## 1. Threat Assessment: Subprocess Execution on Windows Hosts

### Critical Security Finding:
The baseline `ProcessIsolatedSandbox` previously executed child Python processes via `subprocess.Popen([sys.executable, "-I", "solution.py"])`.

While this baseline enforced:
1. Isolated temporary directory (`tempfile.TemporaryDirectory`)
2. Execution timeouts (`subprocess.TimeoutExpired`)
3. Sanitized environment variables (stripping `SECRET_KEY`)
4. Standard output/error byte ceilings (64 KB)

**IT DOES NOT CONSTITUTE A TRUE SECURITY BOUNDARY AGAINST MALICIOUS UNTRUSTED CODE.**

### Concrete Host Exploitation Vectors:
1. **Filesystem Traversal & Data Theft:** Even with an isolated `cwd`, a child process running under the same Windows user token can execute:
   ```python
   # Can read entire drive despite isolated cwd
   with open("C:/Users/User/.ssh/id_rsa", "r") as f: data = f.read()
   ```
2. **Network Egress / Command & Control:** The child process inherits the host network stack. A submission could establish reverse TCP shells or exfiltrate environment data to external servers.
3. **Host Process Fork Bombs:** Subprocess spawning cannot be completely restricted on Windows without Job Objects or kernel containerization.

---

## 2. Hardened Sandbox Security Policy

To guarantee compliance with **Rule 14 ("Do not use unsafe code execution methods")**:

1. **Host Subprocess Execution Is Explicitly Prohibited:**
   - The sandbox supervisor now inspects `settings.SANDBOX_MODE`.
   - When running on a host without verified container isolation, `SANDBOX_MODE` is set to `disabled`.
   - Any attempt to run arbitrary code immediately returns:
     ```json
     {
       "status": "EXECUTION_BLOCKED_SECURITY_POLICY",
       "stderr": "Security Policy: Arbitrary code execution is disabled on this host runtime. A hardened container isolation worker (e.g. Docker / gVisor) is required to execute untrusted code safely."
     }
     ```
2. **Zero Unsafe Fallback:** The system will **never** silently fall back to host subprocess execution if a container worker is absent.

---

## 3. Production Container Isolation Specification (Target: Phase 5)

For Phase 5 (Coding Arena), code execution will only run inside a dedicated, isolated container worker defined in `infrastructure/docker-compose.yml`:
- **Docker Flags:**
  - `--network none` (Total network egress disablement)
  - `--read-only` (Root filesystem mounted read-only)
  - `--tmpfs /tmp:rw,noexec,nosuid,size=32m` (Ephemeral memory-backed scratch space)
  - `--memory 128m --memory-swap 128m` (Strict memory ceiling)
  - `--cpus 1.0` (Strict CPU ceiling)
  - `--user 1000:1000` (Unprivileged non-root user)
  - `--cap-drop ALL` (Drop all Linux kernel capabilities)
  - `--pids-limit 64` (Prevent fork-bomb resource exhaustion)
