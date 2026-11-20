# NEXORA AI - Security Architecture & Threat Defense Matrix

**Document Version:** 1.0  
**Phase:** Phase 1 Foundation  
**Date:** November 19, 2026  

---

## 1. Threat Modeling & Defense In Depth

NEXORA AI enforces security at every layer of the architecture:

```
[ Client Requests (Web / Mobile) ]
                │
                ▼
  [ API Gateway & CORS / Rate Limiter ]
  - Sliding-window rate limit (IP & User ID)
  - CORS whitelist (strict allowed origins)
  - TLS termination & Security headers (HSTS, CSP, X-Frame-Options)
                │
                ▼
  [ Authentication & Role Verification ]
  - JWT Dual-token (Short-lived access 15m, secure HttpOnly refresh 7d)
  - Bcrypt / SHA-256 salted password hashing
  - Server-side RBAC guards (STUDENT, ADMIN, PLACEMENT_CELL)
                │
                ▼
  [ Business Logic & IDOR Defense ]
  - Inherent user ID ownership check on every query
  - Input sanitization (prevent stored XSS & prompt injections)
                │
                ▼
  [ Persistence & Isolated Execution ]
  - Parameterized ORM queries (zero raw SQL concatenation)
  - Dual-tier process sandbox with zero host secret leakage
```

---

## 2. Core Security Controls

### A. Authentication & Session Management
- Passwords hashed with salt before storage.
- JWT tokens signed with 256-bit secret key loaded exclusively from environment.
- Refresh tokens are revocable and bound to user sessions.

### B. Inherent IDOR (Insecure Direct Object Reference) Prevention
- In traditional insecure architectures, an endpoint like `GET /api/v1/resumes/{resume_id}` reads directly from the database using only the path parameter.
- In NEXORA AI, every data access query binds `WHERE id = :resume_id AND user_id = :current_user_id` unless the requesting user possesses verified `ADMIN` privileges.

### C. Isolated Code Execution Security (Sandbox)
- The coding sandbox worker runs submissions in a dedicated scratch directory jail (`tempfile.TemporaryDirectory`).
- Subprocess execution strips all application secrets, API keys, and environment variables.
- Execution timeout kills runaway processes after 3–5 seconds.
- Output is truncated at 64 KB to eliminate buffer overflow / memory flooding attacks.

### D. File Upload Security
- Resumes and documents undergo strict MIME validation, file extension whitelisting (`.pdf`, `.docx`), and file size limits (5 MB max).
- Uploaded files are renamed using UUIDs to prevent directory traversal attacks (`../../evil.sh`).
