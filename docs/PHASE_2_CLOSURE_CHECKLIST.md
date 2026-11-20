# NEXORA AI — Phase 2 Closure & Live Database Checklist
## Comprehensive Human Operator Verification & Sign-off Guide

**Workspace:** `E:\NEXORA_AI`  
**Current Phase:** Phase 2 (Database Architecture, Models, Authentication & RBAC)  
**Status:** All Static Audits & Safe Unit Tests Passed (37/37 passing, 5 skipped pending PG)  
**Target Database:** PostgreSQL 17 (Windows x64 Service `postgresql-x64-17`)  
**Authorization to Start Phase 3:** STRICTLY PENDING SIGN-OFF  

---

## Pre-Execution Gate (Automated Agent Invariants)

- [x] Workspace verified as `E:\NEXORA_AI`.
- [x] All 346 feature requirements preserved in `docs/MASTER_FEATURE_REGISTRY.md`.
- [x] Python test suite executed (37 passed, 5 skipped, 0 failed, exit code 0).
- [x] Feature registry validator executed (`scripts/validate_feature_registry.py`, exit code 0).
- [x] PostgreSQL provisioning script audited for least privilege (`LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS`).
- [x] Unconditional `\password` calls eliminated from routine provisioning.
- [x] Preflight existence check halts if `nexora_dev` or `nexora_test` pre-exists.
- [x] Zero PostgreSQL DDL/DML executed by agent.
- [x] Zero modifications made to `backend/.env`.
- [x] Coding arena host execution prohibited.

---

## Human Operator Execution Steps (Sequential)

### Step 1: Provision Dedicated PostgreSQL Role & Databases
Choose **Option A** (`psql`) or **Option B** (`pgAdmin 4`):

#### Option A: Via `psql` (Recommended)
Open PowerShell and run:
```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -h 127.0.0.1 -f "E:\NEXORA_AI\scripts\postgres\provision_nexora_db.sql"
```
*Provide the `postgres` administrator password when prompted. The script will halt safely if pre-existing databases or unexpected role memberships are found.*

#### Option B: Via `pgAdmin 4`
Open pgAdmin 4 and follow [`scripts/postgres/provision_nexora_db_pgadmin.sql`](file:///e:/NEXORA_AI/scripts/postgres/provision_nexora_db_pgadmin.sql) sequentially:
1. Run **Phase 1** against the `postgres` default database.
2. In object browser, right click `nexora_app` -> **Properties** -> **Definition** -> set password (Phase 2).
3. Run **Phase 3** statements individually with Auto-commit ON.
4. Open Query Tool on `nexora_dev` and execute **Phase 4**.
5. Open Query Tool on `nexora_test` and execute **Phase 5**.
6. Run **Phase 6** verification queries.

---

### Step 2: Set Initial Password for `nexora_app` (CLI Path)
If using Option A, set the password interactively:
```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -h 127.0.0.1 -c "\password nexora_app"
```
*(Enter a strong password. Characters are masked).*

---

### Step 3: Configure `backend/.env`
Update `backend/.env` with your URL-encoded credentials (RFC 3986):
```ini
DATABASE_URL=postgresql+asyncpg://nexora_app:<URL_ENCODED_PASSWORD>@127.0.0.1:5432/nexora_dev
TEST_DATABASE_URL=postgresql+asyncpg://nexora_app:<URL_ENCODED_PASSWORD>@127.0.0.1:5432/nexora_test
```
*(Example: if password contains `@`, encode as `%40`).*

---

### Step 4: Run Alembic Database Migration
Apply schema migrations to the newly created `nexora_dev` database:
```powershell
cd E:\NEXORA_AI\backend
python -m alembic upgrade head
```
*Expected: Revision `831b7c542bb8` executes, creating all 8 tables, indexes, and constraints.*

---

### Step 5: Execute Live PostgreSQL Integration Tests
Run the dedicated live PostgreSQL integration test suite:
```powershell
cd E:\NEXORA_AI
$env:PYTHONPATH="E:\NEXORA_AI"
pytest tests/integration/test_postgresql_integration_live.py -v
```
*Expected: 5/5 tests passing.*

---

### Step 6: Full Regression Verification
Run the entire project test suite against live PostgreSQL:
```powershell
cd E:\NEXORA_AI
$env:PYTHONPATH="E:\NEXORA_AI"
pytest tests/ sandbox/ -v
```
*Expected: 42/42 tests passing.*

---

## Phase 2 Final Sign-Off Gate

| Item | Requirement | Human Verification | Date |
|---|---|---|---|
| PostgreSQL Role Created | `nexora_app` least privilege | [ ] Confirmed | |
| Databases Created | `nexora_dev`, `nexora_test` owned by `nexora_app` | [ ] Confirmed | |
| Alembic Migration | Head revision `831b7c542bb8` applied | [ ] Confirmed | |
| Live PG Integration Suite | 5/5 tests passing | [ ] Confirmed | |
| Full Regression Suite | 42/42 tests passing | [ ] Confirmed | |
| Phase 3 Authorization | Granted by human lead | [ ] Authorized | |
