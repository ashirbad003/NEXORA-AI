"""
NEXORA AI - Phase 13A Disaster Recovery & Backup Engine Test Suite
Comprehensive testing:
- Manifest generation and validation
- FAT32 chunk splitting and reconstruction
- SHA-256 integrity checks
- SQLite online backup consistency
- Isolated restoration and schema verification
- Negative test cases: missing chunks, altered chunks, invalid manifests, prohibited targets
"""

import os
import json
import sqlite3
import shutil
import tempfile
import unittest
from pathlib import Path
from backend.app.core.backup_engine import (
    DisasterRecoveryEngine,
    BackupSecurityError,
    BackupIntegrityError,
    calculate_sha256
)


class TestPhase13ADisasterRecovery(unittest.TestCase):
    def setUp(self):
        # Dedicated, isolated disposable sandbox for test artifacts
        self.test_root = Path(tempfile.mkdtemp(prefix="nexora_dr_test_")).resolve()
        self.backup_root = self.test_root / "backups"
        self.source_db = self.test_root / "source.db"
        self.restored_db = self.test_root / "restored_isolated.db"

        # Populate source DB with synthetic data
        conn = sqlite3.connect(str(self.source_db))
        conn.execute("PRAGMA user_version = 42;")
        conn.execute("""
            CREATE TABLE students (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                readiness_score INTEGER NOT NULL
            );
        """)
        conn.execute("""
            CREATE TABLE flashcard_decks (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                card_count INTEGER DEFAULT 0
            );
        """)
        conn.execute("""
            CREATE TABLE mistake_logs (
                id TEXT PRIMARY KEY,
                problem_id TEXT NOT NULL,
                error_type TEXT NOT NULL,
                occurrence_count INTEGER DEFAULT 1
            );
        """)

        # Insert synthetic data rows
        conn.execute("INSERT INTO students VALUES ('s1', 'alice@nexora.test', 'Alice Student', 85);")
        conn.execute("INSERT INTO students VALUES ('s2', 'bob@nexora.test', 'Bob Learner', 92);")
        conn.execute("INSERT INTO flashcard_decks VALUES ('d1', 'Algorithms & Data Structures', 25);")
        conn.execute("INSERT INTO mistake_logs VALUES ('m1', 'prob_101', 'OffByOneError', 3);")
        conn.commit()
        conn.close()

        # Engine with small chunk size (1 KiB) to thoroughly test chunking logic
        self.engine = DisasterRecoveryEngine(
            backup_root=self.backup_root,
            chunk_size_bytes=1024  # 1 KiB chunks
        )

    def tearDown(self):
        if self.test_root.exists():
            shutil.rmtree(self.test_root, ignore_errors=True)

    def test_01_backup_manifest_generation(self):
        """Verify backup generates valid manifest with correct schema and chunks."""
        manifest = self.engine.backup_sqlite(self.source_db)

        self.assertIn("backup_id", manifest)
        self.assertEqual(manifest["status"], "COMPLETED")
        self.assertEqual(manifest["database_type"], "sqlite")
        self.assertEqual(manifest["schema_user_version"], 42)
        self.assertEqual(manifest["table_count"], 3)
        self.assertIn("students", manifest["tables"])
        self.assertIn("flashcard_decks", manifest["tables"])
        self.assertIn("mistake_logs", manifest["tables"])
        self.assertGreater(manifest["chunk_count"], 1)

        snapshot_dir = self.backup_root / "snapshots" / manifest["backup_id"]
        manifest_file = snapshot_dir / "manifest.json"
        self.assertTrue(manifest_file.exists())

        with open(manifest_file, "r", encoding="utf-8") as f:
            saved_manifest = json.load(f)
        self.assertEqual(saved_manifest["backup_id"], manifest["backup_id"])
        self.assertEqual(saved_manifest["archive_sha256"], manifest["archive_sha256"])

    def test_02_sha256_verification_success(self):
        """Verify checksum integrity check succeeds on untampered backup."""
        manifest = self.engine.backup_sqlite(self.source_db)
        snapshot_dir = self.backup_root / "snapshots" / manifest["backup_id"]

        report = self.engine.verify_backup(snapshot_dir)
        self.assertEqual(report["status"], "VERIFIED")
        self.assertEqual(report["chunk_count_verified"], manifest["chunk_count"])
        self.assertEqual(report["archive_sha256_verified"], manifest["archive_sha256"])

    def test_03_isolated_restoration_and_integrity(self):
        """Verify restoration into isolated target matches synthetic source data and passes PRAGMA integrity_check."""
        manifest = self.engine.backup_sqlite(self.source_db)
        snapshot_dir = self.backup_root / "snapshots" / manifest["backup_id"]

        restore_report = self.engine.restore_sqlite(
            snapshot_path=snapshot_dir,
            target_restore_path=self.restored_db,
            expected_tables=["students", "flashcard_decks", "mistake_logs"]
        )

        self.assertEqual(restore_report["status"], "RESTORED_AND_VERIFIED")
        self.assertEqual(restore_report["integrity_check"], "ok")
        self.assertEqual(restore_report["table_count"], 3)

        # Inspect restored database contents
        conn = sqlite3.connect(str(self.restored_db))
        cursor = conn.cursor()

        students = cursor.execute("SELECT id, email, full_name, readiness_score FROM students ORDER BY id").fetchall()
        self.assertEqual(len(students), 2)
        self.assertEqual(students[0], ('s1', 'alice@nexora.test', 'Alice Student', 85))
        self.assertEqual(students[1], ('s2', 'bob@nexora.test', 'Bob Learner', 92))

        decks = cursor.execute("SELECT id, title, card_count FROM flashcard_decks").fetchall()
        self.assertEqual(decks, [('d1', 'Algorithms & Data Structures', 25)])

        mistakes = cursor.execute("SELECT id, problem_id, error_type, occurrence_count FROM mistake_logs").fetchall()
        self.assertEqual(mistakes, [('m1', 'prob_101', 'OffByOneError', 3)])

        user_version = cursor.execute("PRAGMA user_version").fetchone()[0]
        self.assertEqual(user_version, 42)
        conn.close()

    def test_04_prohibited_restore_destinations_fail_closed(self):
        """Security guard: prevent restoration into live application/dev database paths."""
        manifest = self.engine.backup_sqlite(self.source_db)
        snapshot_dir = self.backup_root / "snapshots" / manifest["backup_id"]

        for prohibited_name in ["nexora_dev.db", "nexora_prod.db", "production.db"]:
            bad_target = self.test_root / prohibited_name
            with self.assertRaises(BackupSecurityError):
                self.engine.restore_sqlite(snapshot_dir, bad_target)

    def test_05_negative_missing_chunk_detection(self):
        """Tamper test: missing chunk must abort verification and restore."""
        manifest = self.engine.backup_sqlite(self.source_db)
        snapshot_dir = self.backup_root / "snapshots" / manifest["backup_id"]

        # Delete one chunk
        chunk_to_remove = snapshot_dir / "chunks" / manifest["chunks"][0]["name"]
        chunk_to_remove.unlink()

        with self.assertRaises(BackupIntegrityError):
            self.engine.verify_backup(snapshot_dir)

        with self.assertRaises(BackupIntegrityError):
            self.engine.restore_sqlite(snapshot_dir, self.restored_db)

    def test_06_negative_altered_chunk_content_detection(self):
        """Tamper test: altered byte in chunk must fail closed with SHA-256 mismatch."""
        manifest = self.engine.backup_sqlite(self.source_db)
        snapshot_dir = self.backup_root / "snapshots" / manifest["backup_id"]

        chunk_to_alter = snapshot_dir / "chunks" / manifest["chunks"][0]["name"]
        with open(chunk_to_alter, "r+b") as f:
            byte = f.read(1)
            f.seek(0)
            f.write(b"\x00" if byte != b"\x00" else b"\xff")

        with self.assertRaises(BackupIntegrityError):
            self.engine.verify_backup(snapshot_dir)

        with self.assertRaises(BackupIntegrityError):
            self.engine.restore_sqlite(snapshot_dir, self.restored_db)

    def test_07_negative_missing_manifest_detection(self):
        """Tamper test: missing manifest.json must fail closed."""
        manifest = self.engine.backup_sqlite(self.source_db)
        snapshot_dir = self.backup_root / "snapshots" / manifest["backup_id"]

        manifest_file = snapshot_dir / "manifest.json"
        manifest_file.unlink()

        with self.assertRaises(BackupIntegrityError):
            self.engine.verify_backup(snapshot_dir)

    def test_08_fat32_chunk_sizing_boundary(self):
        """Verify that every chunk strictly obeys the configured maximum chunk boundary."""
        manifest = self.engine.backup_sqlite(self.source_db)
        for chunk in manifest["chunks"]:
            self.assertLessEqual(chunk["size_bytes"], 1024)

    def test_09_collision_resistance(self):
        """Verify collision prevention when attempting to reuse an existing backup ID."""
        manifest = self.engine.backup_sqlite(self.source_db, backup_id="fixed_backup_id")
        with self.assertRaises(BackupSecurityError):
            self.engine.backup_sqlite(self.source_db, backup_id="fixed_backup_id")


if __name__ == "__main__":
    unittest.main()
