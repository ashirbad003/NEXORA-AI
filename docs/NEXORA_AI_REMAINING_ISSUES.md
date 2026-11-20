# NEXORA AI — Remaining Issues & Infrastructure Limitations

**Date:** 2026-11-20  
**Workspace:** `E:\NEXORA_AI`  
**Current Phase:** Phase 2 Closed, Phase 3 Implemented & Verified  

---

## 1. Documented Infrastructure Limitations (Low/Informational)

### Issue 1: Live PostgreSQL Service Provisioning Awaiting Human Administrator
- **Severity:** Medium (Operational Dependency)
- **Status:** Documented & Runbook Authored
- **Description:** PostgreSQL 17 is installed and active on the host machine (`127.0.0.1:5432`), but creating dedicated databases (`nexora_dev`, `nexora_test`) and role credentials (`nexora_app`) requires local human administrator authentication. The agent is policy-restricted from executing DDL or resetting superuser credentials.
- **Resolution Plan:** The human administrator executes `scripts/postgres/provision_nexora_db.sql` via `psql` or `pgAdmin 4`, configures `backend/.env`, and runs `alembic upgrade head`.

### Issue 2: Coding Arena Hardened Container Worker (Scheduled for Phase 5)
- **Severity:** Low (Deferred Scope by Design)
- **Status:** Intentionally Disabled & Guarded
- **Description:** Unisolated execution of student-submitted code on the host machine is strictly prohibited. The coding sandbox worker is kept in `disabled` mode until containerized/microVM isolation is built in Phase 5.
- **Resolution Plan:** Build Docker container worker with cgroups, memory limits, CPU caps, and non-root execution during Phase 5.

### Issue 3: FAT32 Volume File System Patch
- **Severity:** Low (Environment Specific)
- **Status:** Mitigated via `patch_fs.js`
- **Description:** Workspace resides on volume `E:`, which is a FAT32 filesystem where Node.js `fs.readlink` emits `EISDIR` instead of `EINVAL` on regular files, causing webpack snapshot errors during Next.js builds.
- **Resolution Plan:** Resolved permanently by invoking `node patch_fs.js` preloader in `NODE_OPTIONS` during Next.js builds.
