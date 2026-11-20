# NEXORA AI — Phase 0–4 Security Audit

**Project:** NEXORA AI  
**Workspace:** `E:\NEXORA_AI`  
**Date:** 2026-11-20  
**Security Lead:** Senior DevSecOps & Security Reviewer  
**Audit Standard:** OWASP Top 10 API Security Risks & Production Hardening Baseline

---

## 1. Security Architecture Assessment

### 1.1 Authentication & Credential Storage
- **Password Hashing:** Implemented with `argon2-cffi` (Argon2id profile). Constant-time verification is enforced. Salting is cryptographically unique per user. Empty passwords, malformed hashes, and injection payloads are rejected.
- **Access Tokens:** Short-lived JWTs (15-minute expiration) signed with HS256 and verified asynchronously.
- **Refresh Tokens:** Long-lived rotating tokens (7-day expiration). Each refresh rotates the token atomically in PostgreSQL.
- **Token Family Revocation:** Verified by `test_audit_01_token_reuse_family_revocation`. Attempting to present a previously rotated refresh token causes the system to revoke the entire family of active refresh tokens associated with that user session.

### 1.2 Authorization & Access Control (RBAC & IDOR)
- **Role Enforcement:** 4 distinct system roles (`STUDENT`, `RECRUITER`, `PLACEMENT_CELL`, `ADMIN`). Protected endpoints employ FastAPI dependency injection (`require_roles(...)`) to enforce authorization before route handler execution.
- **IDOR Immunity:** Student endpoints (profile, topic progress, notes) extract user identity directly from the authenticated JWT claims rather than trusting client-supplied URL parameters or JSON payloads.
- **Cross-Role Segregation:** Students attempting to access administrative endpoints (`/admin/users`, `/admin/audit-logs`) receive HTTP 403 Forbidden.

### 1.3 Code Execution & Coding Arena Isolation
- **Sandbox Status:** `SANDBOX_MODE="disabled"`.
- **Enforcement:** `sandbox/service.py` intercepts any attempt to execute arbitrary code when sandbox mode is unisolated, returning an immediate security error.
- **Subprocess Host Fallback:** Strictly prohibited. Automated tests (`sandbox/tests/test_sandbox_baseline.py`) confirm that unisolated host code execution is blocked.

### 1.4 Database Security & Input Sanitation
- **ORM Parameterization:** All database queries utilize SQLAlchemy 2.0 with asyncpg driver, eliminating raw SQL concatenation and SQL injection vulnerabilities.
- **Secret Zero-Exposure:** Database credentials and JWT secrets are loaded via environment variables (`.env`). No secrets are printed to logs, exposed via error traces, or committed to version control.

---

## 2. Threat Vector Matrix

| OWASP API Category | Vulnerability Risk | Mitigation Implemented | Verified Test Case | Status |
| :--- | :--- | :--- | :--- | :---: |
| **API1:2023** | Broken Object Level Auth (BOLA / IDOR) | JWT claim identity binding on student data | `test_pg_05_idor_protection` | SECURE |
| **API2:2023** | Broken Authentication | Argon2id + rotating JWT + token reuse revocation | `test_audit_01_token_reuse_family_revocation` | SECURE |
| **API3:2023** | Broken Object Property Auth | Pydantic response models restrict sensitive fields | `test_01_student_profile_update...` | SECURE |
| **API4:2023** | Unrestricted Resource Consumption | Pagination on admin queries; algorithm step limits | `test_03_admin_paginated_users...` | SECURE |
| **API5:2023** | Broken Function Level Auth | RBAC decorator with role-based claim checking | `test_07_rbac_admin_endpoint_forbidden` | SECURE |
| **API6:2023** | Server-Side Request Forgery (SSRF) | AI provider calls use validated internal configurations | `test_ai_provider_abstraction_local` | SECURE |
| **API8:2023** | Security Misconfiguration | Production security headers, CORS origin validation | `test_health_live_endpoint` | SECURE |
| **Host Escape** | Arbitrary Code Execution | Sandbox engine disabled until isolated containers exist | `test_arbitrary_code_blocked...` | SECURE |

---

## 3. Residual Security Findings & Recommendations

1. **Coding Arena Hardening (Future Milestone):**
   - *Current state:* Sandbox is disabled.
   - *Requirement:* Before enabling `SANDBOX_MODE="enabled"`, implement an isolated gVisor or Docker worker container with strict cgroups, memory limits (128MB), CPU quotas (0.5 CPU), and disabled network access (`--network none`).
2. **Rate Limiting:**
   - *Current state:* Login and refresh endpoints validate credentials securely.
   - *Recommendation:* Introduce Redis-backed IP/user rate limiting (e.g. 5 attempts / min) before public deployment to prevent brute-force attacks.
