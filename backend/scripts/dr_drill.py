"""
NEXORA AI - Disaster Recovery Drill Script
Used to execute isolated synthetic disaster recovery simulation and measure precise performance metrics.
"""

import time
import os
import sqlite3
import shutil
import tempfile
from pathlib import Path
from backend.app.core.backup_engine import DisasterRecoveryEngine


def run_drill():
    drill_dir = Path(tempfile.mkdtemp(prefix="nexora_drill_")).resolve()
    source_db = drill_dir / "source_drill.db"
    backup_root = drill_dir / "backups"
    target_restore = drill_dir / "restored_drill.db"

    try:
        # 1. Create synthetic database with multiple realistic tables
        conn = sqlite3.connect(str(source_db))
        conn.execute("CREATE TABLE users (id TEXT PRIMARY KEY, email TEXT, role TEXT);")
        conn.execute("CREATE TABLE activity_log (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, action TEXT, created_at REAL);")
        for i in range(1000):
            conn.execute("INSERT INTO users VALUES (?, ?, ?)", (f"u_{i}", f"user_{i}@nexora.ai", "STUDENT"))
            conn.execute("INSERT INTO activity_log (user_id, action, created_at) VALUES (?, ?, ?)", (f"u_{i}", "LOGIN", time.time()))
        conn.commit()
        conn.close()

        source_size = source_db.stat().st_size
        print(f"SYNTHETIC_DB_SIZE_BYTES: {source_size}")

        # 2. Run backup and measure
        engine = DisasterRecoveryEngine(backup_root=backup_root, chunk_size_bytes=64 * 1024)  # 64 KiB chunks
        t0 = time.perf_counter()
        manifest = engine.backup_sqlite(source_db)
        backup_duration = time.perf_counter() - t0
        print(f"BACKUP_DURATION_SEC: {backup_duration:.4f}")
        print(f"CHUNK_COUNT: {manifest['chunk_count']}")
        print(f"ARCHIVE_SIZE_BYTES: {manifest['archive_size_bytes']}")

        # 3. Verify backup and measure
        snapshot_dir = backup_root / "snapshots" / manifest["backup_id"]
        t0 = time.perf_counter()
        verify_report = engine.verify_backup(snapshot_dir)
        verify_duration = time.perf_counter() - t0
        print(f"VERIFY_DURATION_SEC: {verify_duration:.4f}")
        print(f"VERIFY_STATUS: {verify_report['status']}")

        # 4. Restore and measure
        t0 = time.perf_counter()
        restore_report = engine.restore_sqlite(snapshot_dir, target_restore, expected_tables=["users", "activity_log"])
        restore_duration = time.perf_counter() - t0
        print(f"RESTORE_DURATION_SEC: {restore_duration:.4f}")
        print(f"RESTORE_STATUS: {restore_report['status']}")
        print(f"TOTAL_RECOVERY_TIME_SEC: {(backup_duration + verify_duration + restore_duration):.4f}")

        # 5. Validate row counts
        conn2 = sqlite3.connect(str(target_restore))
        u_cnt = conn2.execute("SELECT COUNT(*) FROM users;").fetchone()[0]
        a_cnt = conn2.execute("SELECT COUNT(*) FROM activity_log;").fetchone()[0]
        conn2.close()
        print(f"RESTORED_USER_ROWS: {u_cnt}")
        print(f"RESTORED_ACTIVITY_ROWS: {a_cnt}")

    finally:
        shutil.rmtree(drill_dir, ignore_errors=True)


if __name__ == "__main__":
    run_drill()
