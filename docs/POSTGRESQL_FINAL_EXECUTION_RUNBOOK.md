# NEXORA AI — PostgreSQL Final Provisioning & Verification Runbook
## Phase 2 Closure & Safe Database Execution Guide

**Workspace:** `E:\NEXORA_AI`  
**Target PostgreSQL Version:** PostgreSQL 17 (x64 Windows Service `postgresql-x64-17`)  
**Target Application Role:** `nexora_app` (Least Privilege)  
**Target Databases:** `nexora_dev` (Development), `nexora_test` (Testing)  
**Workflow Paradigm:** **Fail-Closed Greenfield Provisioning**  
**Document Status:** Ready for Manual Administrator Execution  

---

## 1. Pre-Execution Safety Checklist

Before running any script or issuing database commands, verify each item:

- [ ] **Workspace Integrity:** Confirm current directory is `E:\NEXORA_AI`.
- [ ] **Registry Integrity:** Verify `docs/MASTER_FEATURE_REGISTRY.md` contains all 346 features intact.
- [ ] **PostgreSQL Service State:** Confirm the PostgreSQL 17 Windows service is running on port 5432:
  ```powershell
  Get-Service -Name postgresql-x64-17
  & "C:\Program Files\PostgreSQL\17\bin\pg_isready.exe" -h 127.0.0.1 -p 5432
  ```
- [ ] **No Guessing / Overwriting:** Do NOT run commands to drop databases or reset the `postgres` superuser password.
- [ ] **Zero Credential Exposure:** Never record plain passwords in batch scripts, SQL files, or version control.
- [ ] **Connection String Safety:** Ensure that special characters in passwords will be URL-encoded (RFC 3986) before saving to `.env`.

---

## 2. Execution Procedure Option A: Interactive `psql` CLI (Recommended)

This procedure executes [`scripts/postgres/provision_nexora_db.sql`](file:///e:/NEXORA_AI/scripts/postgres/provision_nexora_db.sql) using the official PostgreSQL client.

### Step 1: Execute Provisioning Script
Open Windows PowerShell (Run as Administrator or as your local user) and execute:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -h 127.0.0.1 -f "E:\NEXORA_AI\scripts\postgres\provision_nexora_db.sql"
```
*Note:* You will be prompted for the existing `postgres` superuser password to connect.

### Step 2: Observe Preflight & Automation Behavior
- **Recursive Membership Audit:** If `nexora_app` belongs directly or indirectly to elevated roles, the script stops immediately with:
  `ERROR: SAFETY STOP: Role nexora_app has direct or indirect membership in: [...]`
- **Database Collision Check:** If `nexora_dev` or `nexora_test` already exists (under any owner), the script stops immediately with:
  `ERROR: SAFETY STOP: Target database(s) already exist: [...]`
- **Fail-Closed Notice:** The workflow will not modify, drop, or alter permissions of existing databases. If you intended to re-use an existing database, follow Section 5 below.
- If preflights pass, the script idempotently creates/enforces `nexora_app`, creates `nexora_dev` and `nexora_test`, configures permissions, and prints verification tables.

### Step 3: Set Application Password (Initial Provisioning Only)
If this is the first time `nexora_app` is being provisioned, run interactive `psql` to set its password:

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -h 127.0.0.1 -c "\password nexora_app"
```
*Note:* Type your chosen strong application password when prompted. The terminal will mask typed characters.

*(If you are running routine provisioning and `nexora_app` already has an active password, SKIP Step 3 to preserve existing credentials).*

---

## 3. Execution Procedure Option B: Staged pgAdmin 4 GUI

If preferred, use pgAdmin 4 following [`scripts/postgres/provision_nexora_db_pgadmin.sql`](file:///e:/NEXORA_AI/scripts/postgres/provision_nexora_db_pgadmin.sql).

> [!IMPORTANT]
> Do NOT execute the file as a single continuous block. PostgreSQL does not permit `CREATE DATABASE` inside transaction blocks. Follow the phases below in order.

### Phase 1: Preflight Audit & Role Setup
1. Open pgAdmin 4.
2. In the Browser tree, connect to the local PostgreSQL 17 server.
3. Open the **Query Tool** connected to the default `postgres` database.
4. Execute **Step 1A** (checks direct & nested role memberships via recursive CTE). Verify no unexpected memberships exist.
5. Execute **Step 1B** (checks database existence). If `nexora_dev` or `nexora_test` is listed, **STOP** and do not proceed.
6. Execute **Step 1C** (enforces role attributes `LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS`).

### Phase 2: Set Initial Password (GUI Object Browser)
*(Skip this phase if `nexora_app` already has an active password).*
1. In the pgAdmin tree, expand **Login/Group Roles**.
2. Right-click **`nexora_app`** and select **Properties...**.
3. Go to the **Definition** tab.
4. Enter your chosen strong password in the **Password** field.
5. Click **Save**.

### Phase 3: Discrete Database Creation
1. In the Query Tool connected to `postgres` (ensure Auto-commit is ON in tool settings):
2. Highlight and execute **Step 3A**:
   ```sql
   CREATE DATABASE nexora_dev OWNER nexora_app ENCODING 'UTF8';
   ```
3. Highlight and execute **Step 3B**:
   ```sql
   CREATE DATABASE nexora_test OWNER nexora_app ENCODING 'UTF8';
   ```

### Phase 4 & Phase 5: Schema & Permission Configuration
1. In the pgAdmin tree, right-click **`nexora_dev`** and select **Query Tool**.
2. Execute all queries in **PHASE 4** of `provision_nexora_db_pgadmin.sql`.
3. In the pgAdmin tree, right-click **`nexora_test`** and select **Query Tool**.
4. Execute all queries in **PHASE 5** of `provision_nexora_db_pgadmin.sql`.

### Phase 6: Run Verification Queries
Run the verification queries from Phase 6 to confirm role flags, database owners, and schema privileges.

---

## 4. Application Configuration (`backend/.env`) & URL-Encoding Rules

When the database password has been established, the connection string in `backend/.env` must be configured.

### URL-Encoding Guidelines (RFC 3986):
PostgreSQL connection URIs format credentials as:
`postgresql+asyncpg://<username>:<password>@<host>:<port>/<database>`

If your password contains special characters, they **must be URL-encoded**:
| Character | Encoded Value |
|---|---|
| `@` | `%40` |
| `:` | `%3A` |
| `/` | `%2F` |
| `?` | `%3F` |
| `#` | `%23` |
| `%` | `%25` |
| `&` | `%26` |
| `+` | `%2B` |
| `=` | `%3D` |

**Example:**  
If password is `P@ss+word#123`:  
Encoded: `P%40ss%2Bword%23123`  
Connection URI:  
`DATABASE_URL=postgresql+asyncpg://nexora_app:P%40ss%2Bword%23123@127.0.0.1:5432/nexora_dev`  
`TEST_DATABASE_URL=postgresql+asyncpg://nexora_app:P%40ss%2Bword%23123@127.0.0.1:5432/nexora_test`

---

## 5. Manual Recovery After Partial Provisioning or Existing Database Conflict

If the provisioning script fails closed because `nexora_dev` or `nexora_test` already exists:
1. **Audit Owner and Contents:** Run `SELECT datname, pg_get_userbyid(datdba) FROM pg_database WHERE datname IN ('nexora_dev', 'nexora_test');`.
2. **If Existing Databases are Abandoned / Empty:** You may manually drop them in psql: `DROP DATABASE nexora_dev; DROP DATABASE nexora_test;`, then re-run `provision_nexora_db.sql`.
3. **If Existing Databases Belong to Another System:** Choose a distinct database name for NEXORA AI, update the provisioning script, and update `.env`.

---

## 6. Explicit List of Remaining Human Administrator Actions

The automated AI environment is strictly prohibited from running PostgreSQL DDL, connecting to PostgreSQL, or altering user secrets. To close Phase 2, the human administrator must perform the following actions:

1. **Execute Provisioning Script:** Run Procedure A (`psql`) or Procedure B (`pgAdmin 4`).
2. **Set `nexora_app` Password:** Execute `\password nexora_app` in `psql` or use pgAdmin GUI.
3. **Configure `backend/.env`:** Populate `DATABASE_URL` and `TEST_DATABASE_URL` with the URL-encoded credentials.
4. **Run Live Migrations & Integration Suite:**
   - Apply migrations to `nexora_dev`:
     ```powershell
     cd E:\NEXORA_AI\backend
     python -m alembic upgrade head
     ```
   - Run live PostgreSQL integration tests:
     ```powershell
     cd E:\NEXORA_AI
     $env:PYTHONPATH="E:\NEXORA_AI"
     pytest tests/integration/test_postgresql_integration_live.py -v
     ```
5. **Phase 2 Closure Sign-off:** Complete the checklist in [`docs/PHASE_2_CLOSURE_CHECKLIST.md`](file:///e:/NEXORA_AI/docs/PHASE_2_CLOSURE_CHECKLIST.md) and authorize commencement of Phase 3.
