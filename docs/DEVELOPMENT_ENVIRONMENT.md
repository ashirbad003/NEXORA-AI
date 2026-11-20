# NEXORA AI - Development Environment & Storage Architecture

**Document Version:** 1.0  
**Phase:** Phase 1 Foundation  
**Workspace:** `E:\NEXORA_AI`  
**Date:** November 19, 2026  

---

## 1. Storage Architecture Assessment

### Physical Storage Characteristics:
- **Active Workspace Location:** `E:\NEXORA_AI`
- **Device Description:** Generic Removable Storage Device (USB 3.2 Gen 1 / USB Bus)
- **Filesystem Type:** `FAT32`
- **Capacity:** 58.58 GB total, 58.58 GB free
- **Host Alternative Drives:**
  - Drive `C:` NVMe SSD (15.01 GB free, NTFS)
  - Drive `D:` NVMe SSD Partition (108.38 GB free, NTFS)

### FAT32 Operational Constraints & Mitigation Strategy:
1. **4 GB File-Size Ceiling:**
   - *Constraint:* FAT32 cannot store any file larger than 4,294,967,295 bytes (4 GB).
   - *Impact on NEXORA AI:* Large database backups, full monolithic docker images, or uncompressed machine learning model weights exceeding 4 GB will throw write errors.
   - *Mitigation:* Database backup procedures are configured to use **split gzip chunking** (chunks capped at 1.0 GB).
2. **I/O Latency on Deep Directories (e.g. `node_modules`):**
   - *Constraint:* FAT32 lacks indexing performance found in NTFS and ext4, resulting in higher latency during directory traversals with tens of thousands of small files.
   - *Mitigation:* Keep root dependencies clean and focused. Use flat dependency layouts and exclude caches from git and search indexing.
3. **Absence of POSIX Permissions:**
   - *Constraint:* FAT32 does not store file execution flags (`chmod +x`).
   - *Mitigation:* Scripts are invoked explicitly with their runtimes (e.g., `python scripts/...` or `node scripts/...`). Process-level permissions for sandbox execution are controlled in memory and OS process creation tokens.
4. **Workspace Confinement Policy:**
   - In accordance with Mandatory Rule 1 and Rule 2, the primary workspace remains anchored in `E:\NEXORA_AI`. Relocating the active project root to Drive `D:` requires explicit user authorization.

---

## 2. Verified Toolchain Matrix

| Runtime / Tool | Detected Version | Purpose |
|---|---|---|
| **Python** | `3.13.14` | Backend FastAPI core, AI abstraction engine, Sandbox supervisor, test suites |
| **pip** | `26.1.2` | Python package management |
| **Node.js** | `v24.19.0` | Next.js 14+ App Router frontend, TypeScript compilation |
| **npm** | `11.17.0` | Node.js package management |
| **Git** | `2.55.0.windows.3` | Source version control |
| **Docker CLI** | `29.9.3` | Container deployment client |
| **Docker Daemon** | Stopped / Inactive | Documented limitation; dual-tier sandbox ensures zero dependency on live daemon for local dev/test |
