# NEXORA AI — PostgreSQL Provisioning Safety Review
## Script Inspection, Least-Privilege Verification & Safe Execution Protocol

**Date:** 2026-11-19  
**Workspace:** `E:\NEXORA_AI`  
**Target Database:** `nexora_dev` and `nexora_test`  
**Target Role:** `nexora_app`  
**Auditor:** Principal Database Architect & Application Security Engineer  
**Script Under Audit:** `E:\NEXORA_AI\scripts\postgres\provision_nexora_db.sql`  
**Review Status:** **PASSED ALL 12 MANDATORY SAFETY VERIFICATION GATES**  

---

## 1. Itemized Pre-Execution Safety Verification

| Gate | Verification Requirement | Assessment & Evidence | Status |
|---|---|---|---|
| **1** | **Role Creation Idempotency** | Uses `DO $do$ ... IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'nexora_app')`. Creating `nexora_app` when it already exists updates attributes without error. | **PASS** |
| **2** | **No Unexpected Role Modification** | Only operates on role `nexora_app`. No `postgres` or existing third-party roles are altered. | **PASS** |
| **3** | **No Drop / Overwrite of Databases** | Uses `SELECT 'CREATE DATABASE ...' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '...')\gexec`. Never calls `DROP DATABASE`, `ALTER DATABASE RENAME`, or destructive operations. | **PASS** |
| **4** | **Database Creation Outside Transaction** | Uses `\gexec` in `psql` to execute individual `CREATE DATABASE` commands outside a `BEGIN ... COMMIT` block, adhering to PostgreSQL requirements. | **PASS** |
| **5** | **No Superuser Privileges** | Explicitly specifies `NOSUPERUSER` in both `CREATE ROLE` and `ALTER ROLE`. Role has no administrative access to server configuration or file systems. | **PASS** |
| **6** | **Disabled CREATEDB & CREATEROLE** | Explicitly specifies `NOCREATEDB NOCREATEROLE NOINHERIT`. Role cannot spawn additional databases or grant privileges. | **PASS** |
| **7** | **Explicit Privileges Configured** | Configures `GRANT CONNECT, TEMPORARY ON DATABASE ...`, `GRANT USAGE, CREATE ON SCHEMA public ...`, and `ALTER DEFAULT PRIVILEGES ... GRANT ALL ON TABLES/SEQUENCES`. | **PASS** |
| **8** | **Ownership for Alembic Migrations** | `nexora_dev` and `nexora_test` are created with `OWNER nexora_app`. This ensures Alembic can run DDL (`CREATE TABLE`, `CREATE INDEX`, `ALTER TABLE`) without requiring superuser. | **PASS** |
| **9** | **Zero Hardcoded Passwords** | Uses `\prompt 'Enter secure password for nexora_app: ' app_password` and `ALTER ROLE ... WITH PASSWORD :'app_password'`. Zero plaintext passwords or placeholder tokens are saved in the file. | **PASS** |
| **10** | **Secure Local Password Entry** | Handled interactively by `psql` in the local terminal session. Never transmitted to chat, logs, or external tools. | **PASS** |
| **11** | **Tool Compatibility** | `scripts/postgres/provision_nexora_db.sql` is optimized for `psql` (utilizing `\prompt`, `\gexec`, `\connect`). A dedicated companion script [`scripts/postgres/provision_nexora_db_pgadmin.sql`](file:///e:/NEXORA_AI/scripts/postgres/provision_nexora_db_pgadmin.sql) is provided for pgAdmin 4 GUI users. | **PASS** |
| **12** | **Repeat Execution Safety** | The script can be run repeatedly without errors or damage to existing database state or schemas. | **PASS** |

---

## 2. Password Character Encoding & Connection String Analysis

When configuring the connection URL in `backend/.env`:
```
postgresql+asyncpg://<username>:<password>@<host>:<port>/<database>
```

### Critical URL-Encoding Rules for Passwords:
Database connection URLs follow RFC 3986 URI standard. If the password for `nexora_app` contains special characters, they **MUST be percent-encoded (URL-encoded)** to prevent connection string parsing errors.

| Character | Percent-Encoded String | Example Plaintext | Example in Connection URL |
|---|---|---|---|
| `@` | `%40` | `Pass@123` | `Pass%40123` |
| `/` | `%2F` | `Pass/123` | `Pass%2F123` |
| `:` | `%3A` | `Pass:123` | `Pass%3A123` |
| `#` | `%23` | `Pass#123` | `Pass%23123` |
| `$` | `%24` | `Pass$123` | `Pass%24123` |
| `%` | `%25` | `Pass%123` | `Pass%25123` |
| `&` | `%26` | `Pass&123` | `Pass%26123` |
| `+` | `%2B` | `Pass+123` | `Pass%2B123` |
| `?` | `%3F` | `Pass?123` | `Pass%3F123` |

#### Python Helper to URL-Encode a Password:
```python
from urllib.parse import quote_plus
encoded_password = quote_plus("YourStrongPasswordHere!@#$")
print(f"postgresql+asyncpg://nexora_app:{encoded_password}@127.0.0.1:5432/nexora_dev")
```

---

## 3. Exact Safe Execution Instructions

### Option 1: Via `psql` Command Line (Recommended)
1. Open PowerShell on Windows.
2. Run the provisioning script as the postgres administrator:
   ```powershell
   & "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -h 127.0.0.1 -f "E:\NEXORA_AI\scripts\postgres\provision_nexora_db.sql"
   ```
3. When prompted, enter the password for `postgres` to authenticate.
4. When prompted by `Enter secure password for nexora_app: `, type your desired password and hit Enter.
5. The script will safely provision `nexora_app`, `nexora_dev`, and `nexora_test`.

### Option 2: Via pgAdmin 4 (GUI)
1. Open **pgAdmin 4** and connect to your local server.
2. Open the **Query Tool** on database `postgres`.
3. Open [`scripts/postgres/provision_nexora_db_pgadmin.sql`](file:///e:/NEXORA_AI/scripts/postgres/provision_nexora_db_pgadmin.sql).
4. Replace `CHANGE_ME_IN_PGADMIN_SECURE_PASSWORD` with your password.
5. Execute the script steps.

---

## 4. Post-Execution Activation Steps

Once provisioned:
1. Create `backend/.env` with your URL-encoded credentials:
   ```bash
   DATABASE_URL=postgresql+asyncpg://nexora_app:<ENCODED_PASSWORD>@127.0.0.1:5432/nexora_dev
   TEST_DATABASE_URL=postgresql+asyncpg://nexora_app:<ENCODED_PASSWORD>@127.0.0.1:5432/nexora_test
   ```
2. Verify migrations and live test execution:
   ```powershell
   alembic upgrade head
   python -m unittest tests/integration/test_postgresql_integration_live.py -v
   ```
