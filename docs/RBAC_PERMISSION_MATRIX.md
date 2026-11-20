# NEXORA AI — RBAC Permission & Authorization Matrix
## Declarative Server-Side Access Control Specification

**Date:** 2026-11-19  
**Version:** 1.0 (Phase 2 Baseline)  
**Strategy:** Server-Side Enforced Role-Based Access Control (RBAC)  

---

## 1. System Roles Hierarchy

NEXORA AI recognizes four primary operational roles in its identity model:

1. **`ADMIN` (`admin`)**:
   System administrators with global oversight, telemetry monitoring, user role promotion, system configuration, and audit inspection.
2. **`PLACEMENT_CELL` (`placement_cell`)**:
   Institutional officers managing campus recruitment drives, company assessments, student verification, and placement reporting.
3. **`STUDENT` (`student`)**:
   Primary learners preparing for technical interviews, solving problems, training with AI, building resumes, and applying for positions.
4. **`RECRUITER` (`recruiter`)**:
   Corporate talent scouts reviewing candidate profiles, posting hiring assessments, and scheduling technical interviews.

---

## 2. Declarative Route Dependencies

Role checks are strictly enforced in FastAPI route decorators using dependency injection (`backend/app/api/deps.py`):

```python
# Requiring Student role
@router.get("/profile/{student_user_id}", dependencies=[Depends(require_roles([UserRole.STUDENT, UserRole.ADMIN]))])
async def get_student_profile(...):
    ...

# Requiring Admin role only
@router.get("/admin/users", dependencies=[Depends(require_roles([UserRole.ADMIN]))])
async def list_users(...):
    ...

# Requiring Placement Cell role or Admin
@router.get("/placement/overview", dependencies=[Depends(require_roles([UserRole.PLACEMENT_CELL, UserRole.ADMIN]))])
async def get_placement_overview(...):
    ...
```

---

## 3. Comprehensive RBAC Endpoint Permission Matrix

| Module / Route | HTTP Method | Public | Student | Admin | Placement Cell | Recruiter | Ownership Scoping (IDOR Protection) |
|---|---|---|---|---|---|---|---|
| `/api/v1/auth/register/student` | `POST` | YES | NO | NO | NO | NO | N/A |
| `/api/v1/auth/login` | `POST` | YES | NO | NO | NO | NO | N/A |
| `/api/v1/auth/refresh` | `POST` | YES | NO | NO | NO | NO | Cryptographic Hash Check |
| `/api/v1/auth/logout` | `POST` | NO | YES | YES | YES | YES | Own User Tokens Only |
| `/api/v1/auth/me` | `GET` | NO | YES | YES | YES | YES | Own Profile Only (`current_user`) |
| `/api/v1/students/profile/{id}` | `GET` | NO | YES (Own) | YES (All) | YES (All) | YES (Approved) | `current_user.id == target_id` |
| `/api/v1/admin/users` | `GET` | NO | NO | YES | NO | NO | Admin Scope |
| `/api/v1/admin/audit-logs` | `GET` | NO | NO | YES | NO | NO | Admin Scope |
| `/api/v1/placement/overview` | `GET` | NO | NO | YES | YES | NO | Institution Scope |
| `/health/live` | `GET` | YES | YES | YES | YES | YES | None |
| `/health/ready` | `GET` | YES | YES | YES | YES | YES | None |

---

## 4. Insecure Direct Object Reference (IDOR) Scoping Rules

Role validation alone is insufficient to protect sensitive resources. An authenticated student must never be allowed to access or mutate another student's data.

### Enforced Ownership Rule:
When accessing student profile `GET /api/v1/students/profile/{student_user_id}`:
```python
if UserRole.ADMIN not in user_roles and UserRole.PLACEMENT_CELL not in user_roles:
    if current_user.id != student_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You can only access your own profile."
        )
```
This guarantees strict tenant isolation at the request boundary.
