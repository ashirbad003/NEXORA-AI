# NEXORA AI — Security Audit & Threat Risk Assessment
## Phases 0 through 3 Deep Technical Evaluation

**Date:** 2026-11-20  
**Workspace:** `E:\NEXORA_AI`  
**Scope:** Authentication, Cryptography, RBAC, Database Security, Sandbox Execution Boundary, and API Surface

---

## 1. Authentication & Cryptography Review

### Argon2id Password Hashing
- **Algorithm:** Argon2id (`argon2_cffi`)
- **Parameters:**
  - Memory Cost: 65,536 KiB (64 MiB)
  - Time Cost: 3 iterations
  - Parallelism: 4 lanes
- **Assessment:** Conforms strictly to OWASP and RFC 9106 guidelines. Constant-time verification is enforced. Salting is cryptographically unique per hash. Malformed hashes and empty passwords reject cleanly without crashing.

### JWT Access & Refresh Token Architecture
- **Access Tokens:** Signed with HMAC-SHA256, 15-minute expiration time, carries user ID, email, and array of assigned roles.
- **Refresh Tokens:** Cryptographically random (32 bytes / 256 bits of entropy), stored hashed (SHA-256) in PostgreSQL (`refresh_tokens.token_hash`), 7-day expiration time.
- **Token Rotation & Family Revocation:** Every refresh call consumes the presented token and issues a new pair. If an already-revoked token is presented (reuse attempt), the entire token family (`user_id`) is revoked immediately, forcing re-authentication.
- **Atomic Concurrency:** Concurrency tests confirm that simultaneous refresh requests allow exactly one request to succeed while subsequent calls receive HTTP 401.

---

## 2. Authorization & Inherent IDOR Protection

### Role-Based Access Control (RBAC)
- **Roles:** `STUDENT`, `ADMIN`, `PLACEMENT_CELL`.
- **Default Policy:** Deny-by-default. Endpoints use FastAPI dependency guards (`require_roles([UserRoleEnum.ADMIN])`, etc.).
- **Boundary Verification:**
  - `STUDENT` cannot access `/api/v1/admin/users`, `/api/v1/admin/audit-logs`, or `/api/v1/placement/students` (HTTP 403 Forbidden).
  - `PLACEMENT_CELL` cannot access admin endpoints.

### Query-Level IDOR Protection
- `/api/v1/students/profile/{user_id}` validates that the requester matches `user_id` unless the requester possesses the `ADMIN` role. Students attempting to inspect or mutate another student's profile receive HTTP 403 Forbidden.

---

## 3. Database Security & Privilege Hardening

- **PostgreSQL 17 System:** `127.0.0.1:5432`.
- **Role Isolation:** Database application role `nexora_app` has `NOSUPERUSER`, `NOCREATEDB`, `NOCREATEROLE`, `NOINHERIT`, `NOREPLICATION`, and `NOBYPASSRLS`.
- **Credential Storage:** Stored exclusively in local `backend/.env`. Excluded by `.gitignore` and omitted from terminal outputs.
- **SQL Injection Prevention:** 100% of database interactions utilize SQLAlchemy 2.0 async ORM with parameterized query compilation. Zero raw SQL string interpolation is permitted.

---

## 4. Coding Arena Sandbox Isolation Guardrail

- **Vulnerability Analyzed:** Executing untrusted student-submitted code on the Windows host.
- **Safeguard Invariant:**
  - `SANDBOX_MODE` is configured to `"disabled"`.
  - `ProcessIsolatedSandbox` explicitly halts execution if `SANDBOX_MODE != "container_isolated"`.
  - Child subprocess execution on the host is strictly prohibited.
- **Status:** **SECURE & BLOCKED**. Host-level arbitrary execution is prevented by policy until Phase 5 Docker containerization is integrated.

---

## 5. Security Summary Matrix

| Category | Control | Status | Evidence |
|---|---|---|---|
| Passwords | Argon2id RFC 9106 | VERIFIED | `tests/unit/test_password_security.py` |
| Tokens | JWT + SHA-256 Rotating Refresh | VERIFIED | `tests/integration/test_phase_2_security_deep_audit.py` |
| Token Reuse | Family Revocation | VERIFIED | `test_audit_01_token_reuse_family_revocation` |
| Concurrency | Atomic Refresh Locking | VERIFIED | `test_audit_02_concurrent_refresh_requests` |
| Access Control | Strict RBAC Dependencies | VERIFIED | `test_07_rbac_admin_endpoint_forbidden_to_student` |
| Data Isolation | Inherent IDOR Guards | VERIFIED | `test_06_idor_student_profile_defense` |
| Database | Non-superuser `nexora_app` | VERIFIED | Live PostgreSQL 17 Catalog Audit |
| Code Execution | Host Execution Fail-Closed | VERIFIED | `sandbox/tests/test_sandbox_baseline.py` |
