# NEXORA AI — Phase 5 Security Audit

**Project:** NEXORA AI  
**Workspace:** `E:\NEXORA_AI`  
**Phase:** 5 (Coding Arena & Isolated Sandbox Worker)  
**Date:** 2026-11-20  
**Security Lead:** Senior DevSecOps & Security Reviewer  
**Audit Standard:** Host Containment, OWASP Top 10 API Security & Untrusted Execution Boundaries

---

## 1. Sandbox Isolation & Untrusted Code Execution Boundary

### 1.1 Invariant: Prohibition of Direct Host Subprocess Execution
- **Threat:** On Windows, executing student code via standard `subprocess.Popen` runs under the host user session. A student submitting `import os; os.system(...)` or socket connections can read host files, spawn background miners, or attack internal networks.
- **Enforcement:** `sandbox/worker.py` enforces a strict gate:
  - If `settings.SANDBOX_MODE != "container_isolated"` or the container daemon is offline, all execution requests are immediately rejected with `EXECUTION_BLOCKED_SECURITY_POLICY`.
  - No fallback to host subprocess execution is permitted.
  - Verified by automated tests `test_arbitrary_code_blocked_when_unisolated` and `test_subprocess_host_fallback_prohibited`.

### 1.2 Container Sandbox Guardrails (When Enabled)
- **Non-Root & Network Isolation:** `--network none` flag is mandatory. Untrusted containers have 0 network interfaces.
- **Resource Limits:** `--memory 128m`, `--cpus 0.5`, `--pids-limit 64` (fork-bomb immunity).
- **Filesystem Immutability:** `--read-only` root filesystem.
- **Timeout Ceilings:** Python `subprocess.TimeoutExpired` terminates running containers after 3 seconds, returning `TIME_LIMIT_EXCEEDED`.

---

## 2. API Security, Data Protection & IDOR Immunity

### 2.1 Hidden Test Case Shielding (FEAT-068)
- Problem details fetched by students (`GET /api/v1/coding/problems/{slug}`) strictly query `ProblemTestCase.is_sample == True`.
- Secret/hidden test cases and expected outputs are never returned to the frontend or included in error traces.
- Verified by `test_03_problem_detail_and_hidden_test_case_protection`.

### 2.2 IDOR & Submission History Isolation (FEAT-073)
- Submissions endpoint (`GET /api/v1/coding/submissions/me`) binds directly to `current_user.id` extracted from validated JWT access tokens.
- Cross-student submission tampering is structurally impossible.
- Verified by `test_05_submission_evaluation_and_history`.

### 2.3 Sanitized Stderr & Truncation (FEAT-072)
- Execution outputs and error messages are truncated to 64KB (`max_output_bytes = 65536`) to prevent memory exhaustion / DoS from infinite loop printing.

---

## 3. Overall Security Audit Verdict

**AUDIT VERDICT: FULL GO (PASSED)**
- Zero host-level code execution vulnerabilities.
- Zero credential exposure.
- All 13 API routes protected with RBAC and JWT validation.
