import os

manifest_path = "docs/BACKUP_MANIFEST_PHASE_0_TO_4.md"
included_files = []
for root, dirs, files in os.walk(r"E:\NEXORA_AI"):
    if any(p in root for p in [".git", "node_modules", ".next", "__pycache__", ".pytest_cache"]):
        continue
    for f in files:
        if f.endswith(".db") or f == ".env":
            continue
        rel = os.path.relpath(os.path.join(root, f), r"E:\NEXORA_AI")
        included_files.append(rel.replace("\\", "/"))

with open(manifest_path, "w", encoding="utf-8") as out:
    out.write("# NEXORA AI — Phase 0–4 Backup Manifest\n\n")
    out.write("**Date:** 2026-11-20\n")
    out.write("**Local Backup Location:** `E:\\NEXORA_AI_BACKUP_20261120_175139`\n")
    out.write(f"**Total Preserved Files:** {len(included_files)}\n\n")
    out.write("## Excluded Sensitive & Generated Files (Zero-Leakage Policy)\n")
    out.write("- `backend/.env` (Local PostgreSQL database credentials and JWT secrets)\n")
    out.write("- `nexora_dev.db` (Local SQLite test database)\n")
    out.write("- `frontend/node_modules/` (Vendor dependencies)\n")
    out.write("- `frontend/.next/` (Build output traces)\n")
    out.write("- `.pytest_cache/` & `__pycache__/` (Binary bytecode & test cache)\n\n")
    out.write("## Preserved File Inventory\n")
    for f in sorted(included_files):
        out.write(f"- `{f}`\n")

print(f"Manifest written with {len(included_files)} files.")
