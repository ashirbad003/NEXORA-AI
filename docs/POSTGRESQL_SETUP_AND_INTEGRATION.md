# NEXORA AI — PostgreSQL 17 Setup, Integration & Credential Provisioning Specification
## Server Architecture, Least-Privilege Role Setup, Database Isolation & Connection Runbook

**Date:** 2026-11-19  
**Workspace:** `E:\NEXORA_AI`  
**Database Server:** PostgreSQL 17 (Windows x86_64, Port 5432)  
**Target Database:** `nexora_dev` & `nexora_test`  
**Application Role:** `nexora_app` (Least Privilege)  
**Provisioning Script:** `scripts/postgres/provision_nexora_db.sql`  

---

## 1. Executive Summary & Provisioning Gate Status

During Phase 2 final closure, all architectural, driver, dialect, connection pooling, and test artifacts for PostgreSQL 17 integration were completed and verified:
1. **Windows Service:** `postgresql-x64-17` verified running on `127.0.0.1:5432` (`pg_isready` returns `accepting connections`).
2. **Python Driver:** `asyncpg` (v0.32.0) installed and verified alongside `psycopg2-binary` (v2.9.13).
3. **Connection Pooling:** SQLAlchemy 2.0 `AsyncAdaptedQueuePool` configured in `backend/app/db/session.py`.
4. **Dialect Fail-Safe:** Engine explicitly rejects invalid dialects to prevent silent fallbacks to SQLite in production.
5. **Idempotent SQL Script:** Authored [`scripts/postgres/provision_nexora_db.sql`](file:///e:/NEXORA_AI/scripts/postgres/provision_nexora_db.sql) to provision role `nexora_app` and databases `nexora_dev` and `nexora_test`.
6. **Integration Test Suite:** Authored [`tests/integration/test_postgresql_integration_live.py`](file:///e:/NEXORA_AI/tests/integration/test_postgresql_integration_live.py) covering user registration, duplicate email rejection, JWT login, token rotation, atomic concurrency, and IDOR protection.

### Mandatory Safety Stop Protocol:
In accordance with Section 3 and Section 10 of the Audit Charter (*"If existing administrator credentials are unavailable, stop and request that the user provision the role and database through an authorized PostgreSQL administration interface; do not bypass authentication; do not ask the user to paste passwords into chat or documentation"*):
- Existing superuser passwords were not reset.
- Passwords were not guessed or cracked.
- Live execution against PostgreSQL 17 is held at the **User Provisioning Gate**.

---

## 2. Administrator One-Time Provisioning Action (Manual Step)

To complete the final live connection:

### Option A: Via pgAdmin 4 (GUI)
1. Open **pgAdmin 4** (installed in `C:\Program Files\PostgreSQL\17\pgAdmin 4`).
2. Connect to the local server.
3. Open the Query Tool and paste the contents of [`scripts/postgres/provision_nexora_db.sql`](file:///e:/NEXORA_AI/scripts/postgres/provision_nexora_db.sql).
4. Replace `<REPLACE_WITH_STRONG_PASSWORD>` with a strong password.
5. Execute the script.

### Option B: Via `psql` Command Line
Run PowerShell and execute the provisioning script as the postgres administrator:
```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -h 127.0.0.1 -f "E:\NEXORA_AI\scripts\postgres\provision_nexora_db.sql"
```

---

## 3. Environment Variable Activation (Post-Provisioning)

Once provisioned, configure `backend/.env` (or set environment variables) without pasting credentials into chat or source code:

```bash
# In backend/.env
DATABASE_URL=postgresql+asyncpg://nexora_app:<YOUR_PASSWORD>@127.0.0.1:5432/nexora_dev
TEST_DATABASE_URL=postgresql+asyncpg://nexora_app:<YOUR_PASSWORD>@127.0.0.1:5432/nexora_test
```

### Verification Commands:
```powershell
# 1. Run Alembic migration against PostgreSQL:
alembic upgrade head

# 2. Run the live PostgreSQL integration tests:
python -m unittest tests/integration/test_postgresql_integration_live.py -v
```
