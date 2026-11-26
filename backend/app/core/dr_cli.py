"""
NEXORA AI - Database Disaster Recovery CLI
Command-line interface for performing consistent database backups,
integrity verifications, and isolated test restorations.
"""

import argparse
import sys
import json
from pathlib import Path
from backend.app.core.backup_engine import (
    DisasterRecoveryEngine,
    BackupSecurityError,
    BackupIntegrityError
)


def main():
    parser = argparse.ArgumentParser(description="NEXORA AI Database Disaster Recovery CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create a consistent chunked database backup")
    backup_parser.add_argument("--source", required=True, help="Path to source SQLite database")
    backup_parser.add_argument("--root", default="backups", help="Path to backup storage root")
    backup_parser.add_argument("--chunk-size-mb", type=int, default=500, help="Max chunk size in MiB (default: 500)")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify integrity of an existing backup snapshot")
    verify_parser.add_argument("--snapshot", required=True, help="Path to snapshot directory")

    # Restore command
    restore_parser = subparsers.add_parser("restore", help="Restore backup into an isolated target destination")
    restore_parser.add_argument("--snapshot", required=True, help="Path to snapshot directory")
    restore_parser.add_argument("--target", required=True, help="Path to isolated target database")
    restore_parser.add_argument("--root", default="backups", help="Path to backup storage root")

    args = parser.parse_args()

    try:
        if args.command == "backup":
            engine = DisasterRecoveryEngine(
                backup_root=Path(args.root),
                chunk_size_bytes=args.chunk_size_mb * 1024 * 1024
            )
            manifest = engine.backup_sqlite(Path(args.source))
            print(json.dumps(manifest, indent=2))
            print(f"\n[SUCCESS] Backup completed successfully: {manifest['backup_id']}")
            sys.exit(0)

        elif args.command == "verify":
            engine = DisasterRecoveryEngine()
            report = engine.verify_backup(Path(args.snapshot))
            print(json.dumps(report, indent=2))
            print(f"\n[SUCCESS] Snapshot verified: {report['status']}")
            sys.exit(0)

        elif args.command == "restore":
            engine = DisasterRecoveryEngine(backup_root=Path(args.root))
            report = engine.restore_sqlite(Path(args.snapshot), Path(args.target))
            print(json.dumps(report, indent=2))
            print(f"\n[SUCCESS] Restoration completed and verified: {report['target_restored_path']}")
            sys.exit(0)

    except (BackupSecurityError, BackupIntegrityError, Exception) as e:
        print(f"\n[ERROR] Disaster recovery operation failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
