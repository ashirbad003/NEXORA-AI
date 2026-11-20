import os
import unittest
import sqlite3
import shutil
from datetime import datetime

class TestDatabaseBackupRestore(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.abspath("test_backup_sandbox")
        os.makedirs(self.test_dir, exist_ok=True)
        self.source_db = os.path.join(self.test_dir, "source.db")
        self.backup_db = os.path.join(self.test_dir, "backup.db")
        self.restored_db = os.path.join(self.test_dir, "restored.db")

        # Create source DB with test data
        conn = sqlite3.connect(self.source_db)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE users (id TEXT PRIMARY KEY, email TEXT UNIQUE, full_name TEXT);")
        cursor.execute("INSERT INTO users VALUES ('u1', 'user1@nexora.ai', 'User One');")
        cursor.execute("INSERT INTO users VALUES ('u2', 'user2@nexora.ai', 'User Two');")
        conn.commit()
        conn.close()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_backup_and_restore_integrity(self):
        """Verify logical database backup and restore into a separate disposable database."""
        # 1. Execute online backup
        src_conn = sqlite3.connect(self.source_db)
        bck_conn = sqlite3.connect(self.backup_db)
        src_conn.backup(bck_conn)
        bck_conn.close()
        src_conn.close()

        self.assertTrue(os.path.exists(self.backup_db), "Backup file must exist")
        self.assertGreater(os.path.getsize(self.backup_db), 0, "Backup must be non-empty")

        # 2. Restore into a separate disposable database
        bck_conn = sqlite3.connect(self.backup_db)
        res_conn = sqlite3.connect(self.restored_db)
        bck_conn.backup(res_conn)
        bck_conn.close()

        # 3. Verify restored data
        cursor = res_conn.cursor()
        users = cursor.execute("SELECT id, email, full_name FROM users ORDER BY id;").fetchall()
        res_conn.close()

        self.assertEqual(len(users), 2)
        self.assertEqual(users[0], ('u1', 'user1@nexora.ai', 'User One'))
        self.assertEqual(users[1], ('u2', 'user2@nexora.ai', 'User Two'))

if __name__ == "__main__":
    unittest.main()
