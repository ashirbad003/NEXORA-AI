# NEXORA AI — Database Migration Guide (Alembic)
## Schema Evolution, Migration Procedures & Rollback Runbook

**Date:** 2026-11-19  
**Version:** 1.0 (Phase 2 Baseline)  
**Tools:** Alembic, SQLAlchemy 2.0 Async, aiosqlite / asyncpg  

---

## 1. Migration Architecture Overview

Alembic is configured in `backend/alembic/` to inspect SQLAlchemy models in `backend/app/models/` and emit deterministic Python migration scripts.

### Directory Structure:
```
backend/
├── alembic/
│   ├── env.py                # Async database engine wrapper & target metadata
│   ├── script.py.mako        # Template for new migration revisions
│   └── versions/             # Timestamped migration revisions
│       └── 6193850678ed_initial_core_auth_and_rbac_tables.py
└── alembic.ini               # Central Alembic configuration file
```

---

## 2. Executing Migrations

### 2.1 Applying Pending Migrations (Upgrade)
To apply all unapplied migrations to the target database:
```powershell
cd E:\NEXORA_AI\backend
alembic upgrade head
```

### 2.2 Rolling Back Migrations (Downgrade)
To rollback one revision:
```powershell
cd E:\NEXORA_AI\backend
alembic downgrade -1
```

To rollback all migrations to a completely blank database schema:
```powershell
cd E:\NEXORA_AI\backend
alembic downgrade base
```

### 2.3 Checking Current Schema Version
```powershell
cd E:\NEXORA_AI\backend
alembic current
```

To view the complete historical log of applied and available revisions:
```powershell
cd E:\NEXORA_AI\backend
alembic history --verbose
```

---

## 3. Creating New Schema Migrations (Autogenerate)

Whenever new models are added or existing columns are modified:

1. Update or create the model file in `backend/app/models/`.
2. Ensure the model is imported in `backend/app/models/__init__.py`.
3. Generate the revision script:
   ```powershell
   cd E:\NEXORA_AI\backend
   alembic revision --autogenerate -m "describe_change_here"
   ```
4. **Mandatory Inspection:** Open the generated file in `backend/alembic/versions/` and manually inspect `upgrade()` and `downgrade()` functions. Verify that constraints, default values, and column drops are accurate.
5. Apply the migration to your test database:
   ```powershell
   alembic upgrade head
   ```

---

## 4. Current Baseline Revisions

### Revision `6193850678ed`: Initial Core Auth and RBAC Tables
- **Created Tables:**
  - `roles`
  - `users`
  - `user_roles`
  - `student_profiles`
  - `admin_profiles`
  - `placement_cell_profiles`
  - `refresh_tokens`
  - `audit_logs`
- **Integrity Verified:**
  - Verified `upgrade head` succeeds.
  - Verified `downgrade base` drops all tables cleanly.
  - Verified re-applying `upgrade head` yields a stable schema.
