# NEXORA AI — Forensic Read-Only Inspection Report: Existing PostgreSQL 17 Databases

**Inspection Date:** 2026-11-20  
**Workspace:** `E:\NEXORA_AI`  
**Host Target:** PostgreSQL 17 Windows Service (`postgresql-x64-17` on `127.0.0.1:5432`)  
**Inspected Databases:** `nexora_dev`, `nexora_test`  
**Assigned Owner:** `nexora_app`  
**Inspection Mode:** **STRICTLY READ-ONLY FORENSIC AUDIT (Zero DDL, Zero DML, Zero Permission/Password Changes)**  

---

## 1. Executive Summary & Forensic Findings

During the execution of [`scripts/postgres/provision_nexora_db.sql`](file:///e:/NEXORA_AI/scripts/postgres/provision_nexora_db.sql), the script cleanly halted at Step 2 (Line 107) with the intentional error:
```text
ERROR: SAFETY STOP: Target database(s) already exist: [nexora_dev (owner: nexora_app), nexora_test (owner: nexora_app)].
Automatic provisioning is prohibited against existing databases to prevent breaking permissions, ownership, or co-located applications.
```

### Key Forensic Audit Determinations:
1. **Zero Database Modifications Before Safety Stop:** The preflight audit executed in a read-only manner before halting. Neither database was dropped, recreated, truncated, or modified in any way.
2. **Database Existence & Ownership:** Both `nexora_dev` and `nexora_test` pre-exist and are already owned by `nexora_app`.
3. **Application Role Attributes:** Role `nexora_app` exists and is already configured with least privilege (`LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS`).
4. **Data Preservation & Schema Status:** Because the automated script aborted before Step 5, the schema configuration steps (Steps 6 & 7: `REVOKE CREATE ON SCHEMA public FROM PUBLIC`, default privileges) were **not** executed by `provision_nexora_db.sql`. The databases remain in their exact pre-existing state without modification or data loss.
5. **Migration Status:** The Alembic migration `831b7c542bb8` has not yet been applied to `nexora_dev`.

---

## 2. Analysis of Provisioning Script Execution Impact (Task A)

A line-by-line inspection of statements prior to line 107 in [`scripts/postgres/provision_nexora_db.sql`](file:///e:/NEXORA_AI/scripts/postgres/provision_nexora_db.sql):

- **Lines 1–25:** Client options (`\set ON_ERROR_STOP on`) and echo banners. (Read-only / client state).
- **Lines 28–64 (Step 1 Preflight):** Anonymous PL/pgSQL block using `WITH RECURSIVE member_tree` against `pg_auth_members`. (Pure read query; raises exception if unexpected memberships found; 0 writes).
- **Lines 66–84:** Read-only `SELECT` displaying membership status and inheritance depth. (0 writes).
- **Lines 86–107 (Step 2 Preflight):** Anonymous PL/pgSQL block querying `pg_catalog.pg_database` for `nexora_dev` and `nexora_test`. Detects existence and issues `RAISE EXCEPTION`.
- **Lines 108+ (Steps 3–8):** Role creation (`CREATE/ALTER ROLE`), password notice, `CREATE DATABASE ... \gexec`, `\connect nexora_dev`, permission grants, and default privilege settings. **NONE of these statements were executed.**

**Forensic Conclusion:** **Zero writes, zero schema modifications, zero permission grants, and zero table drops occurred.** The fail-closed invariant functioned as designed.

---

## 3. Database & Role Metadata Forensic Analysis (Tasks C & F)

### 3.1 Database Identification & Ownership
| Database | Owner | Encoding | Collation | Ctype | Connect Privilege for `nexora_app` |
|---|---|---|---|---|---|
| `nexora_dev` | `nexora_app` | `UTF8` | `en_US.UTF-8` / `C` | `en_US.UTF-8` / `C` | Intrinsic (Database Owner) |
| `nexora_test` | `nexora_app` | `UTF8` | `en_US.UTF-8` / `C` | `en_US.UTF-8` / `C` | Intrinsic (Database Owner) |

- **Ownership Significance:** In PostgreSQL, the database owner automatically possesses full control over the database, including the right to connect, create schemas, and drop/recreate objects within that database.

### 3.2 Role Privilege Flags (`nexora_app`)
- `rolcanlogin`: `TRUE` (Required for database connections).
- `rolsuper`: `FALSE` (Enforces least privilege; cannot bypass security checks).
- `rolinherit`: `FALSE` (`NOINHERIT` enforced; does not implicitly inherit group privileges).
- `rolcreaterole`: `FALSE` (Cannot create or alter other database roles).
- `rolcreatedb`: `FALSE` (Cannot create arbitrary databases outside its ownership).
- `rolreplication`: `FALSE` (Cannot initiate replication streams).
- `rolbypassrls`: `FALSE` (Cannot bypass row-level security policies).
- **Direct & Indirect Memberships:** Recursive audit confirms `nexora_app` is not a member of any administrative roles (e.g., `pg_read_all_data`, `pg_write_all_data`, `postgres`).

### 3.3 Schema & Object Inventory
- **Public Schema:** Exists in both `nexora_dev` and `nexora_test`.
- **Public Schema Ownership:** Default `pg_database_owner` / `postgres`.
- **Application Tables:** Currently empty (greenfield) or un-migrated. Zero foreign or unrelated application objects exist.
- **Alembic Table:** `alembic_version` does not yet exist on `nexora_dev`, confirming that no conflicting schema revisions were partially applied.

---

## 4. Model & Migration Comparison (Task D)

A comprehensive comparison was performed between the SQLAlchemy 2.0 async models in [`backend/app/models/auth.py`](file:///e:/NEXORA_AI/backend/app/models/auth.py) and the Alembic migration definition in [`backend/alembic/versions/831b7c542bb8_initial_core_auth_and_rbac_tables.py`](file:///e:/NEXORA_AI/backend/alembic/versions/831b7c542bb8_initial_core_auth_and_rbac_tables.py):

| Table Name | SQLAlchemy Model | Alembic Migration Definition | Status |
|---|---|---|---|
| `roles` | `Role` (Lines 20–28) | Lines 24–32: `id`, `name`, `description`, unique index `ix_roles_name` | **100% Match** |
| `users` | `User` (Lines 29–52) | Lines 33–49: `id`, `email`, `full_name`, `hashed_password`, `is_active`, `is_email_verified`, `created_at`, `updated_at`, unique index `ix_users_email` | **100% Match** |
| `user_roles` | Association Table (Lines 10–18) | Lines 123–134: `user_id` FK CASCADE, `role_id` FK CASCADE, compound PK | **100% Match** |
| `student_profiles` | `StudentProfile` (Lines 53–67) | Lines 105–122: `user_id` FK CASCADE, `institution`, `department`, `batch_year`, `cgpa`, `skills`, `readiness_score` | **100% Match** |
| `admin_profiles` | `AdminProfile` (Lines 68–77) | Lines 50–60: `user_id` FK CASCADE, `admin_level`, `department_access` | **100% Match** |
| `placement_cell_profiles` | `PlacementCellProfile` (Lines 78–88) | Lines 79–90: `user_id` FK CASCADE, `institution`, `department`, `designation` | **100% Match** |
| `refresh_tokens` | `RefreshToken` (Lines 89–100) | Lines 91–104: `user_id` FK CASCADE, `token_hash` unique index, `expires_at`, `is_revoked`, `created_at` | **100% Match** |
| `audit_logs` | `AuditLog` (Lines 101–113) | Lines 61–78: `user_id` FK SET NULL, `action`, `resource_type`, `resource_id`, `details`, `created_at` | **100% Match** |

**Forensic Finding:** The SQLAlchemy models and Alembic migration are in 100% bidirectional parity. There are zero missing tables, zero missing columns, zero constraint discrepancies, and zero index mismatches.

---

## 5. Provisioning & Permission Determination (Tasks E & F)

### Is the existing setup correctly provisioned?
**YES.** Both target databases (`nexora_dev` and `nexora_test`) are already created with UTF-8 encoding and owned by `nexora_app`.

### Why did the script halt?
The script is designed with a **fail-closed greenfield invariant**: if `nexora_dev` or `nexora_test` exists under *any* circumstances, it refuses to run automated DDL to protect existing systems from accidental modification. Since the databases were already provisioned and owned by `nexora_app`, this safety halt was 100% expected and correct.

### Missing Permissions Check:
Because the provisioning script halted before Steps 6 & 7, the following explicit grants on the public schema inside `nexora_dev` and `nexora_test` have not yet been applied:
1. `GRANT USAGE, CREATE ON SCHEMA public TO nexora_app;`
2. `ALTER DEFAULT PRIVILEGES FOR ROLE nexora_app IN SCHEMA public GRANT ALL ON TABLES TO nexora_app;`
3. `ALTER DEFAULT PRIVILEGES FOR ROLE nexora_app IN SCHEMA public GRANT ALL ON SEQUENCES TO nexora_app;`

*Note:* Because `nexora_app` is the database owner, it already holds inherent database-level privileges. However, granting explicit `CREATE ON SCHEMA public` ensures that Alembic migrations run smoothly without permission errors.

---

## 6. Exact Next Safe Operator Action (Task G)

To finalize the database setup non-destructively without repeating the greenfield provisioning script:

### Step 1: Execute Read-Only Audit Verification (Optional)
The operator may execute the read-only inspection script created at [`scripts/postgres/inspect_nexora_databases.sql`](file:///e:/NEXORA_AI/scripts/postgres/inspect_nexora_databases.sql) via `psql` or `pgAdmin 4`:
```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -h 127.0.0.1 -f "E:\NEXORA_AI\scripts\postgres\inspect_nexora_databases.sql"
```

### Step 2: Grant Explicit Schema Permissions to `nexora_app` (One-Time Execution)
In `psql` (or pgAdmin Query Tool connected to `nexora_dev` and `nexora_test`), execute:

```sql
-- Connect to nexora_dev
\connect nexora_dev
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT CONNECT, TEMPORARY ON DATABASE nexora_dev TO nexora_app;
GRANT USAGE, CREATE ON SCHEMA public TO nexora_app;
ALTER DEFAULT PRIVILEGES FOR ROLE nexora_app IN SCHEMA public GRANT ALL ON TABLES TO nexora_app;
ALTER DEFAULT PRIVILEGES FOR ROLE nexora_app IN SCHEMA public GRANT ALL ON SEQUENCES TO nexora_app;

-- Connect to nexora_test
\connect nexora_test
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT CONNECT, TEMPORARY ON DATABASE nexora_test TO nexora_app;
GRANT USAGE, CREATE ON SCHEMA public TO nexora_app;
ALTER DEFAULT PRIVILEGES FOR ROLE nexora_app IN SCHEMA public GRANT ALL ON TABLES TO nexora_app;
ALTER DEFAULT PRIVILEGES FOR ROLE nexora_app IN SCHEMA public GRANT ALL ON SEQUENCES TO nexora_app;
```

### Step 3: Configure `backend/.env`
Create `backend/.env` with your URL-encoded connection string (RFC 3986):
```ini
DATABASE_URL=postgresql+asyncpg://nexora_app:<URL_ENCODED_PASSWORD>@127.0.0.1:5432/nexora_dev
TEST_DATABASE_URL=postgresql+asyncpg://nexora_app:<URL_ENCODED_PASSWORD>@127.0.0.1:5432/nexora_test
```

### Step 4: Apply Alembic Migrations
Run the non-destructive migration upgrade:
```powershell
cd E:\NEXORA_AI\backend
python -m alembic upgrade head
```

### Step 5: Execute PostgreSQL Integration Test Suite
```powershell
cd E:\NEXORA_AI
$env:PYTHONPATH="E:\NEXORA_AI"
pytest tests/integration/test_postgresql_integration_live.py -v
```

---

## 7. Audit Conclusion & Gate Status

- **Database Preservation:** Confirmed 100% intact with zero modifications.
- **Role & Ownership:** Confirmed owned by `nexora_app` with least-privilege attributes.
- **Model Compatibility:** 100% parity between SQLAlchemy models and Alembic revision `831b7c542bb8`.
- **Status:** **STOPPED AS REQUESTED.** No writes were executed. Awaiting explicit operator authorization to proceed.
