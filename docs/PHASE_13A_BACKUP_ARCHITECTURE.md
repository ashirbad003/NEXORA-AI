# NEXORA AI - Phase 13A Backup & Disaster Recovery Architecture

## 1. System Overview
The Phase 13A Disaster Recovery Engine (`backend/app/core/backup_engine.py`) provides automated, consistent, and cryptographically verified backups for NEXORA AI databases.

It incorporates:
- **Consistent Online SQLite Backups:** Uses the SQLite Online Backup API (`src_conn.backup(bck_conn, pages=100)`) to safely copy live databases page-by-page without prolonged table locking.
- **FAT32-Compatible Chunked Storage:** Bounded multipart chunking (configurable, default 500 MiB, tested down to 1 KiB) ensuring no archive component violates the 4 GiB single-file limit on FAT32 volumes.
- **SHA-256 Cryptographic Integrity:** Generates dual-layer checksums: one for each chunk and one for the reconstructed archive. Restorations fail closed if any checksum mismatch occurs.
- **Collision-Resistant Manifest Metadata:** Each backup directory houses a machine-readable `manifest.json` containing timestamp (UTC), schema version, table counts, chunk mappings, and engine specifications.
- **Fail-Closed Security Guards:** Enforces strict destination guards (`PROHIBITED_RESTORE_FILENAMES`), preventing accidental overwrites of `nexora_dev.db`, `nexora_prod.db`, or live databases.

---

## 2. Directory Layout
```
backup_root/
    snapshots/
        snapshot_<YYYYMMDD_HHMMSSZ>_<entropy>/
            manifest.json
            checksums.sha256
            verification_report.json
            chunks/
                chunk_0000.bin
                chunk_0001.bin
                ...
    temporary/
        tmp_<backup_id>/ (cleaned up on completion)
    reports/
```

---

## 3. Cryptographic Verification & Fail-Closed Guardrails
Before any restoration:
1. Manifest existence and JSON validity are verified.
2. The exact list of chunk files on disk is checked against the manifest chunk definitions.
3. Every chunk's SHA-256 is independently re-computed and validated against the manifest record.
4. Chunks are sequentially streamed into a running SHA-256 calculation to verify the composite archive checksum.
5. If any chunk is missing, modified, or out of sequence, the engine immediately aborts with `BackupIntegrityError`.
6. Restoration target paths are strictly evaluated; if the target file matches any protected database name, the engine aborts with `BackupSecurityError`.
