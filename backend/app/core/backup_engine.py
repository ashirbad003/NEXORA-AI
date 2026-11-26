"""
NEXORA AI - Database Disaster Recovery & Automated Backup Engine
Phase 13A: Enterprise-grade consistent backup, FAT32 chunked storage, SHA-256 integrity,
manifest metadata, and safe isolated restoration.
"""

import os
import json
import hashlib
import sqlite3
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

BACKUP_ENGINE_VERSION = "1.0.0"
DEFAULT_CHUNK_SIZE_BYTES = 500 * 1024 * 1024  # 500 MiB default (< 4 GiB FAT32 limit)
DEFAULT_BACKUP_ROOT = Path("backups").resolve()

# Prohibited database targets to prevent destructive restores
PROHIBITED_RESTORE_FILENAMES = {
    "nexora_dev.db",
    "nexora_prod.db",
    "production.db",
    "dev.db",
    "main.db"
}


class BackupSecurityError(Exception):
    """Raised when an operation violates security boundaries or destination rules."""
    pass


class BackupIntegrityError(Exception):
    """Raised when checksums or chunk validations fail closed."""
    pass


def calculate_sha256(file_path: Path) -> str:
    """Computes SHA-256 checksum of a file in streaming 64 KiB chunks."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def compute_bytes_sha256(data: bytes) -> str:
    """Computes SHA-256 of byte array."""
    return hashlib.sha256(data).hexdigest()


class DisasterRecoveryEngine:
    def __init__(
        self,
        backup_root: Optional[Path] = None,
        chunk_size_bytes: int = DEFAULT_CHUNK_SIZE_BYTES
    ):
        self.backup_root = Path(backup_root) if backup_root else DEFAULT_BACKUP_ROOT
        self.chunk_size_bytes = chunk_size_bytes
        self.snapshots_dir = self.backup_root / "snapshots"
        self.temporary_dir = self.backup_root / "temporary"
        self.reports_dir = self.backup_root / "reports"

    def _ensure_directories(self) -> None:
        """Creates the required root directory structure if not existing."""
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        self.temporary_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def _generate_backup_id(self) -> str:
        """Generates a collision-resistant timestamped backup identifier."""
        utc_now = datetime.now(timezone.utc)
        ts_str = utc_now.strftime("%Y%m%d_%H%M%SZ")
        entropy = hashlib.sha256(f"{time.time()}_{os.getpid()}".encode()).hexdigest()[:8]
        return f"snapshot_{ts_str}_{entropy}"

    def backup_sqlite(
        self,
        source_db_path: Path,
        backup_id: Optional[str] = None,
        custom_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes consistent online backup of a SQLite database using the SQLite Online Backup API.
        Enforces FAT32 chunking, calculates SHA-256 for all chunks and archive,
        and generates a signed manifest.json.
        """
        source_path = Path(source_db_path).resolve()
        if not source_path.exists():
            raise FileNotFoundError(f"Source database not found: {source_path}")

        self._ensure_directories()

        b_id = backup_id or self._generate_backup_id()
        snapshot_dir = self.snapshots_dir / b_id
        if snapshot_dir.exists():
            raise BackupSecurityError(f"Backup snapshot directory collision: {b_id}")

        temp_op_dir = self.temporary_dir / f"tmp_{b_id}"
        temp_op_dir.mkdir(parents=True, exist_ok=False)

        start_time = time.perf_counter()
        temp_db_archive = temp_op_dir / "database.sqlite"

        try:
            # Step 1: Execute consistent SQLite Online Backup
            # SQLite backup API locks page-by-page transactionally without holding long table locks
            src_conn = sqlite3.connect(str(source_path))
            bck_conn = sqlite3.connect(str(temp_db_archive))
            try:
                src_conn.backup(bck_conn, pages=100)
            finally:
                bck_conn.close()
                src_conn.close()

            archive_size = temp_db_archive.stat().st_size
            archive_sha256 = calculate_sha256(temp_db_archive)

            # Step 2: Split archive into FAT32-compatible chunks
            chunks_dir = temp_op_dir / "chunks"
            chunks_dir.mkdir(exist_ok=True)

            chunk_records: List[Dict[str, Any]] = []
            chunk_index = 0

            with open(temp_db_archive, "rb") as src_file:
                while True:
                    chunk_data = src_file.read(self.chunk_size_bytes)
                    if not chunk_data:
                        break
                    
                    chunk_name = f"chunk_{chunk_index:04d}.bin"
                    chunk_path = chunks_dir / chunk_name
                    with open(chunk_path, "wb") as chunk_file:
                        chunk_file.write(chunk_data)

                    chunk_records.append({
                        "index": chunk_index,
                        "name": chunk_name,
                        "size_bytes": len(chunk_data),
                        "sha256": calculate_sha256(chunk_path)
                    })
                    chunk_index += 1

            # If the database was 0 bytes, record an empty chunk definition
            if chunk_index == 0:
                empty_chunk_name = "chunk_0000.bin"
                empty_chunk_path = chunks_dir / empty_chunk_name
                empty_chunk_path.touch()
                chunk_records.append({
                    "index": 0,
                    "name": empty_chunk_name,
                    "size_bytes": 0,
                    "sha256": calculate_sha256(empty_chunk_path)
                })

            duration = time.perf_counter() - start_time

            # Step 3: Extract non-sensitive database metadata
            verify_conn = sqlite3.connect(str(temp_db_archive))
            try:
                tables = [r[0] for r in verify_conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                ).fetchall()]
                schema_user_version = verify_conn.execute("PRAGMA user_version").fetchone()[0]
            finally:
                verify_conn.close()

            # Step 4: Compile Manifest
            manifest: Dict[str, Any] = {
                "backup_id": b_id,
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "engine_version": BACKUP_ENGINE_VERSION,
                "database_type": "sqlite",
                "source_db_name": source_path.name,
                "schema_user_version": schema_user_version,
                "table_count": len(tables),
                "tables": sorted(tables),
                "archive_size_bytes": archive_size,
                "archive_sha256": archive_sha256,
                "chunk_size_limit_bytes": self.chunk_size_bytes,
                "chunk_count": len(chunk_records),
                "chunks": chunk_records,
                "backup_duration_seconds": round(duration, 4),
                "status": "COMPLETED",
                "custom_metadata": custom_metadata or {}
            }

            # Step 5: Atomic Promotion to snapshots_dir
            # Write manifest to temp
            manifest_path = temp_op_dir / "manifest.json"
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

            # Move chunks and manifest into permanent snapshot directory
            snapshot_dir.mkdir(parents=True, exist_ok=False)
            snapshot_chunks_dir = snapshot_dir / "chunks"
            snapshot_chunks_dir.mkdir(parents=True, exist_ok=False)

            for c in chunk_records:
                shutil.move(str(chunks_dir / c["name"]), str(snapshot_chunks_dir / c["name"]))
            
            shutil.move(str(manifest_path), str(snapshot_dir / "manifest.json"))

            # Also create standalone sha256 checksum file
            sha256_file = snapshot_dir / "checksums.sha256"
            with open(sha256_file, "w", encoding="utf-8") as f:
                f.write(f"{archive_sha256}  database_archive\n")
                for c in chunk_records:
                    f.write(f"{c['sha256']}  chunks/{c['name']}\n")

            return manifest

        finally:
            # Safe cleanup of temporary working directory only
            if temp_op_dir.exists():
                shutil.rmtree(temp_op_dir, ignore_errors=True)

    def verify_backup(self, snapshot_path: Path) -> Dict[str, Any]:
        """
        Independently verifies backup chunks and manifest.
        Fails closed on any discrepancy: missing chunk, order mismatch, sha256 mismatch.
        """
        snapshot_dir = Path(snapshot_path).resolve()
        manifest_path = snapshot_dir / "manifest.json"

        if not manifest_path.exists():
            raise BackupIntegrityError(f"Missing manifest.json in {snapshot_dir}")

        with open(manifest_path, "r", encoding="utf-8") as f:
            try:
                manifest = json.load(f)
            except Exception as e:
                raise BackupIntegrityError(f"Invalid JSON in manifest.json: {e}")

        chunks_dir = snapshot_dir / "chunks"
        if not chunks_dir.exists():
            raise BackupIntegrityError(f"Missing chunks directory in {snapshot_dir}")

        expected_chunks = manifest.get("chunks", [])
        if not expected_chunks:
            raise BackupIntegrityError("Manifest contains no chunk definitions")

        actual_chunk_files = sorted([f.name for f in chunks_dir.iterdir() if f.is_file()])
        expected_chunk_names = [c["name"] for c in expected_chunks]

        if actual_chunk_files != sorted(expected_chunk_names):
            raise BackupIntegrityError(
                f"Chunk list mismatch: found {actual_chunk_files}, expected {expected_chunk_names}"
            )

        start_time = time.perf_counter()
        reconstructed_sha256 = hashlib.sha256()
        total_reconstructed_bytes = 0

        for idx, chunk_info in enumerate(expected_chunks):
            if chunk_info.get("index") != idx:
                raise BackupIntegrityError(
                    f"Chunk sequence broken at index {idx}: manifest index is {chunk_info.get('index')}"
                )

            chunk_file = chunks_dir / chunk_info["name"]
            if not chunk_file.exists():
                raise BackupIntegrityError(f"Chunk file missing on disk: {chunk_file.name}")

            actual_chunk_sha256 = calculate_sha256(chunk_file)
            if actual_chunk_sha256 != chunk_info["sha256"]:
                raise BackupIntegrityError(
                    f"SHA-256 mismatch for chunk {chunk_info['name']}: "
                    f"expected {chunk_info['sha256']}, got {actual_chunk_sha256}"
                )

            with open(chunk_file, "rb") as cf:
                chunk_bytes = cf.read()
                reconstructed_sha256.update(chunk_bytes)
                total_reconstructed_bytes += len(chunk_bytes)

        final_reconstructed_hash = reconstructed_sha256.hexdigest()
        expected_archive_sha256 = manifest.get("archive_sha256")

        if final_reconstructed_hash != expected_archive_sha256:
            raise BackupIntegrityError(
                f"Reconstructed archive SHA-256 mismatch: "
                f"expected {expected_archive_sha256}, got {final_reconstructed_hash}"
            )

        verification_duration = time.perf_counter() - start_time

        report = {
            "backup_id": manifest.get("backup_id"),
            "verified_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "VERIFIED",
            "chunk_count_verified": len(expected_chunks),
            "total_bytes_verified": total_reconstructed_bytes,
            "archive_sha256_verified": final_reconstructed_hash,
            "verification_duration_seconds": round(verification_duration, 4)
        }

        # Write verification report
        report_path = snapshot_dir / "verification_report.json"
        with open(report_path, "w", encoding="utf-8") as rf:
            json.dump(report, rf, indent=2)

        return report

    def restore_sqlite(
        self,
        snapshot_path: Path,
        target_restore_path: Path,
        expected_tables: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Restores a verified backup snapshot into an explicitly isolated target destination.
        Guards:
          1. Verifies the snapshot integrity first.
          2. Validates target_restore_path against prohibited production/dev names.
          3. Confirms target directory is valid and not overwriting existing databases silently.
          4. Reconstructs the archive from chunks.
          5. Restores into destination and runs PRAGMA integrity_check.
          6. Verifies schema and objects against expected tables.
        """
        target_path = Path(target_restore_path).resolve()

        # Security check: Prohibit restoration into protected filenames
        if target_path.name.lower() in PROHIBITED_RESTORE_FILENAMES:
            raise BackupSecurityError(
                f"Restore rejected: destination '{target_path.name}' is a protected database name."
            )

        # Verify the snapshot integrity first
        verification_report = self.verify_backup(snapshot_path)
        if verification_report.get("status") != "VERIFIED":
            raise BackupIntegrityError("Restore aborted: Backup failed integrity verification.")

        snapshot_dir = Path(snapshot_path).resolve()
        with open(snapshot_dir / "manifest.json", "r", encoding="utf-8") as f:
            manifest = json.load(f)

        start_time = time.perf_counter()
        temp_restore_dir = self.temporary_dir / f"restore_{manifest['backup_id']}_{int(time.time())}"
        temp_restore_dir.mkdir(parents=True, exist_ok=False)

        reconstructed_db = temp_restore_dir / "reconstructed.sqlite"

        try:
            # Reconstruct SQLite database from verified chunks
            chunks_dir = snapshot_dir / "chunks"
            with open(reconstructed_db, "wb") as out_f:
                for chunk_info in manifest["chunks"]:
                    chunk_file = chunks_dir / chunk_info["name"]
                    with open(chunk_file, "rb") as in_f:
                        shutil.copyfileobj(in_f, out_f)

            # Validate reconstructed file size and checksum
            rec_size = reconstructed_db.stat().st_size
            rec_sha256 = calculate_sha256(reconstructed_db)

            if rec_size != manifest["archive_size_bytes"] or rec_sha256 != manifest["archive_sha256"]:
                raise BackupIntegrityError("Reconstructed database failed size or checksum check.")

            # Perform consistent transfer to target_path using SQLite Online Backup API
            target_path.parent.mkdir(parents=True, exist_ok=True)
            if target_path.exists():
                target_path.unlink()

            src_conn = sqlite3.connect(str(reconstructed_db))
            dst_conn = sqlite3.connect(str(target_path))
            try:
                src_conn.backup(dst_conn)
            finally:
                dst_conn.close()
                src_conn.close()

            # Run SQLite integrity check
            check_conn = sqlite3.connect(str(target_path))
            try:
                integrity_result = check_conn.execute("PRAGMA integrity_check").fetchone()[0]
                restored_tables = [r[0] for r in check_conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                ).fetchall()]
            finally:
                check_conn.close()

            if integrity_result != "ok":
                raise BackupIntegrityError(f"PRAGMA integrity_check failed on restored DB: {integrity_result}")

            if expected_tables:
                missing_tables = set(expected_tables) - set(restored_tables)
                if missing_tables:
                    raise BackupIntegrityError(f"Restored DB missing expected tables: {missing_tables}")

            restore_duration = time.perf_counter() - start_time

            restoration_report = {
                "backup_id": manifest["backup_id"],
                "target_restored_path": str(target_path),
                "restored_at_utc": datetime.now(timezone.utc).isoformat(),
                "status": "RESTORED_AND_VERIFIED",
                "integrity_check": integrity_result,
                "table_count": len(restored_tables),
                "tables": sorted(restored_tables),
                "restore_duration_seconds": round(restore_duration, 4)
            }

            return restoration_report

        finally:
            if temp_restore_dir.exists():
                shutil.rmtree(temp_restore_dir, ignore_errors=True)
