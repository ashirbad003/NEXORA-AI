# NEXORA AI - Phase 13A Disaster Recovery Runbook

## 1. Operational Overview
This runbook details manual and automated procedures for backing up, verifying, and restoring NEXORA AI databases in emergency recovery scenarios.

---

## 2. Command-Line Interface (`dr_cli.py`)

The CLI entrypoint is located at `backend/app/core/dr_cli.py`.

### 2.1 Generating a Backup
To create a consistent, chunked backup of an active SQLite database:
```bash
python -m backend.app.core.dr_cli backup --source path/to/database.db --root backups --chunk-size-mb 500
```
**Output:** Prints the generated `manifest.json` and returns exit code `0` on success.

### 2.2 Verifying a Backup Snapshot
To run independent cryptographic SHA-256 integrity checks against an existing snapshot:
```bash
python -m backend.app.core.dr_cli verify --snapshot backups/snapshots/snapshot_20261126_141600Z_a1b2c3d4
```
**Output:** Generates `verification_report.json` in the snapshot folder and prints the verification summary.

### 2.3 Restoring into an Isolated Target
To restore a snapshot into an isolated destination:
```bash
python -m backend.app.core.dr_cli restore --snapshot backups/snapshots/snapshot_20261126_141600Z_a1b2c3d4 --target isolated_recovery/restored.db --root backups
```
> [!CAUTION]
> The restore target **MUST NEVER** be a live application database path (such as `nexora_dev.db`). The CLI will reject protected database names with `BackupSecurityError`.

---

## 3. Disaster Recovery Drill Procedure
1. Create an isolated directory for disaster recovery verification.
2. Generate synthetic data in a temporary test database.
3. Perform an online backup using `DisasterRecoveryEngine`.
4. Verify the backup with `verify_backup()`.
5. Restore into a newly designated recovery database.
6. Run `PRAGMA integrity_check;` and assert row counts and table presence.
