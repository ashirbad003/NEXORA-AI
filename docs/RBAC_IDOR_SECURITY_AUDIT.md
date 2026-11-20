# NEXORA AI — RBAC & IDOR Security Audit Report
## Server-Side Authorization, Role Enforcement & Object Ownership Boundaries

**Date:** 2026-11-19  
**Workspace:** `E:\NEXORA_AI`  
**Auditor:** Senior Security Architect & QA Auditor  
**Audit Scope:** `backend/app/api/deps.py`, `backend/app/api/students.py`, `backend/app/api/admin.py`, `backend/app/api/placement.py`  
**Verdict:** **PASSED — ZERO PRIVILEGE ESCALATION VULNERABILITIES**  

---

## 1. Executive Summary

A comprehensive authorization and access control audit was conducted on all Phase 2 endpoints. The audit verified:
1. Declarative server-side enforcement of the three core roles: `STUDENT`, `ADMIN`, and `PLACEMENT_CELL`.
2. Negative access testing across all unauthorized role permutations.
3. Insecure Direct Object Reference (IDOR) resistance on user/student data endpoints.
4. Tampering resilience when client headers or request bodies manipulate user identifiers.

**Result:** All endpoints enforce authorization strictly on the backend. Frontend-only visibility controls are not relied upon.

---

## 2. Server-Side RBAC Architecture & Deny-by-Default

Authorization is implemented via FastAPI dependencies (`backend/app/api/deps.py`):
```python
def require_roles(allowed_roles: List[UserRoleEnum]) -> Callable:
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role_names = {r.name for r in current_user.roles}
        required_role_names = {r.value for r in allowed_roles}
        
        if not user_role_names.intersection(required_role_names):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: operation requires one of roles {[r.value for r in allowed_roles]}"
            )
        return current_user
    return role_checker
```

### Security Properties:
- **Deny-by-Default:** If a user possesses no roles or their assigned roles do not intersect with `allowed_roles`, access is rejected with `HTTP 403 Forbidden`.
- **Stateless Verification with State Validation:** While JWT access tokens encode user identity, every request validates that the underlying user account is active in the database before evaluating roles.
- **Fail-Safe Exception Handling:** Malformed bearer tokens, missing authorization headers, or expired tokens reject immediately with `HTTP 401 Unauthorized`.

---

## 3. Negative Access Test Matrix

The following negative tests were executed and passed across the API suite:

| Test Scenario | Target Endpoint | Requesting Identity | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| Unauthenticated call | `GET /api/v1/auth/me` | None (No Token) | `401 Unauthorized` | `401 Unauthorized` | **PASS** |
| Unauthenticated call | `GET /api/v1/admin/users` | None (No Token) | `401 Unauthorized` | `401 Unauthorized` | **PASS** |
| Student -> Admin users | `GET /api/v1/admin/users` | Valid Student | `403 Forbidden` | `403 Forbidden` | **PASS** |
| Student -> Admin logs | `GET /api/v1/admin/audit-logs` | Valid Student | `403 Forbidden` | `403 Forbidden` | **PASS** |
| Student -> Placement list | `GET /api/v1/placement/students` | Valid Student | `403 Forbidden` | `403 Forbidden` | **PASS** |
| Placement -> Admin users | `GET /api/v1/admin/users` | Valid Placement Officer | `403 Forbidden` | `403 Forbidden` | **PASS** |
| Placement -> Admin logs | `GET /api/v1/admin/audit-logs` | Valid Placement Officer | `403 Forbidden` | `403 Forbidden` | **PASS** |
| Placement -> Placement list | `GET /api/v1/placement/students` | Valid Placement Officer | `200 OK` | `200 OK` | **PASS** |
| Admin -> All endpoints | Any Protected Endpoint | Valid Admin | `200 OK` | `200 OK` | **PASS** |
| Deactivated account | Any Protected Endpoint | Deactivated User Token | `403 Forbidden` | `403 Forbidden` | **PASS** |

---

## 4. Insecure Direct Object Reference (IDOR) Audit

### 4.1 Vulnerability Target
`GET /api/v1/students/profile/{student_user_id}` allows querying student profiles by user UUID.

### 4.2 Enforced Object-Level Access Control
In `backend/app/api/students.py`, object ownership is strictly validated before querying the database:
```python
user_role_names = {r.name for r in current_user.roles}
is_staff = bool(user_role_names.intersection({UserRoleEnum.ADMIN.value, UserRoleEnum.PLACEMENT_CELL.value}))

if not is_staff and current_user.id != student_user_id:
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access forbidden: You cannot view another student's profile."
    )
```

### 4.3 Verified Scenarios:
1. **Student A queries Student A (`id == current_user.id`):** Returns `200 OK` with profile payload.
2. **Student A queries Student B (`id != current_user.id`):** Rejected with `403 Forbidden` (`Access forbidden: You cannot view another student's profile`).
3. **Placement Officer queries Student B:** Permitted (`200 OK`) under institutional campus placement oversight.
4. **Platform Administrator queries Student B:** Permitted (`200 OK`) under administrative oversight.

---

## 5. Audit Logging Verification

All security-critical actions generate immutable audit log records via `AuthService.log_audit`:
- **Registration:** Records `STUDENT_REGISTER` with user ID, email, and client IP.
- **Login Success:** Records `LOGIN_SUCCESS` with user ID and client IP.
- **Login Failure:** Records `LOGIN_FAILED` with attempted email and client IP (without storing attempted password).
- **Token Refresh:** Records `TOKEN_REFRESH` with user ID and client IP.
- **Tamper Evidence:** Audit logs maintain a separate append-only structure linked to `users.id ON DELETE SET NULL`, preserving event history even if a user account is purged.
- **Sensitive Data Exclusion:** Verified that passwords, password hashes, secrets, and raw JWT strings are never written to the audit log `details` column.

---

## 6. Audit Verdict

The RBAC implementation and IDOR defenses conform to OWASP API Security standards. Authorization is strictly enforced on the server.
