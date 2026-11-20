# NEXORA AI — Database Backup & Disaster Recovery Verification Report
## Logical Backup Architecture, FAT32 Storage Limits & Disposable Restore Procedures

**Date:** 2026-11-19  
**Workspace:** `E:\NEXORA_AI`  
**Test Harness:** Python `unittest` (`tests/unit/test_backup_restore.py`)  
**Storage Environment:** E: Removable Storage (FAT32 File System)  
**Status:** **VERIFIED (Active Automated Test Passing)**  

---

## 1. Executive Summary

To safeguard platform data against corruption, accidental data loss, or storage failures, NEXORA AI has established a formalized database backup and restore protocol.

This report documents:
1. Automated backup and restore verification through test suite `tests/unit/test_backup_restore.py`.
2. Physical baseline backups of current project state in `backups/`.
3. Recovery runbooks for both SQLite Async (development) and PostgreSQL 17 (production).
4. Storage architecture considerations for removable FAT32 storage (`E:`).

---

## 2. Backup Integrity Test Execution

The automated test `test_backup_and_restore_integrity` in `tests/unit/test_backup_restore.py` was executed as part of the Phase 2 test suite:

```
test_backup_and_restore_integrity (test_backup_restore.TestDatabaseBackupRestore.test_backup_and_restore_integrity)
Verify logical database backup and restore into a separate disposable database. ... ok
```

### Steps Verified by Test:
1. Created populated source database with test records.
2. Executed online logical backup into a separate backup database artifact.
3. Verified backup file creation and non-zero byte size.
4. Restored backup into a completely separate disposable target database.
5. Queried restored table records and verified 100% record match and constraint consistency.

---

## 3. Physical Project Baseline Backup

Prior to Phase 2 final closure, existing configuration and database state were snapshotted in `E:\NEXORA_AI\backups/`:
- `backups/nexora_dev_phase2_baseline.db` (144 KB, contains current users, roles, profiles, tokens, audit logs)
- `backups/alembic.ini.bak` (Alembic configuration backup)

---

## 4. PostgreSQL 17 Backup & Restore Runbook

When running on PostgreSQL 17 in production:

### 4.1 Logical Backup Command (`pg_dump`):
```powershell
# Create custom-format compressed backup with timestamp
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"
& "C:\Program Files\PostgreSQL\17\bin\pg_dump.exe" -h 127.0.0.1 -p 5432 -U nexora_app -F c -b -v -f "D:\NEXORA_BACKUPS\nexora_dev_$TIMESTAMP.dump" nexora_dev
```

### 4.2 Disaster Recovery Procedure (`pg_restore` into Disposable Database):
```powershell
# 1. Create fresh disposable recovery database
& "C:\Program Files\PostgreSQL\17\bin\createdb.exe" -h 127.0.0.1 -p 5432 -U nexora_app nexora_restore_test

# 2. Restore into the disposable database (NEVER overwrite the live database directly)
& "C:\Program Files\PostgreSQL\17\bin\pg_restore.exe" -h 127.0.0.1 -p 5432 -U nexora_app -d nexora_restore_test -v "D:\NEXORA_BACKUPS\nexora_dev_$TIMESTAMP.dump"

# 3. Verify record counts and table integrity
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -h 127.0.0.1 -p 5432 -U nexora_app -d nexora_restore_test -c "SELECT count(*) FROM users;"
```

---

## 5. Storage Architecture & FAT32 File Size Limit Considerations

- **FAT32 Single-File Limit (4 GB):** The project workspace resides on `E:`, formatted as FAT32. Any single file exceeding 4,294,967,295 bytes will fail to write.
- **Remediation & Storage Policy:**
  - Production database dumps and large ML models must **never** be stored on FAT32 partitions.
  - Large backup archives must be directed to NTFS volumes (e.g., `D:\` or cloud storage `gs://` / S3).
  - Production backups must never be committed into the Git repository.
