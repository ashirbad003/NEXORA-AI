# NEXORA AI - Architecture Decisions Record (ADR)

**Document Version:** 1.0  
**Phase:** Phase 0 Independent Audit Gate  
**Date:** November 19, 2026  

---

## ADR-001: Workspace Storage Device (Drive E: FAT32) & Performance Strategy

### Status: ACCEPTED WITH OPERATIONAL MITIGATION

### Context:
The project workspace is located at `E:\NEXORA_AI`. Storage inspection confirms:
- **Device Type:** Removable USB Storage (`Generic STORAGE DEVICE`, BusType USB).
- **Filesystem Type:** `FAT32`.
- **Capacity:** 58.58 GB total, 58.58 GB remaining.
- **Host System Drives:** NVMe SSD 256GB (Drive `C:` ~15.01 GB free, Drive `D:` ~108.38 GB free NTFS).

### Performance & Reliability Implications of FAT32 Removable Storage:
1. **File Size Limit:** FAT32 has an absolute single-file size ceiling of **4 GB (4,294,967,295 bytes)**. Any single database dump, container image, or training weights file exceeding 4 GB will fail to write.
2. **I/O Throughput & Small-File Latency:** USB 2.0/3.0 flash drives exhibit significantly slower random read/write IOPS compared to NVMe SSDs. Deep directory trees with thousands of small files (e.g. `node_modules` with 50,000+ files) will experience elevated install and build times if unmanaged.
3. **Absence of POSIX Permissions / Journaling:** FAT32 does not support native POSIX permissions (`chmod`) or NTFS/ext4 journaling, making it more sensitive to abrupt power loss or USB disconnection during active write streams.
4. **Symlink / Hardlink Limitations:** Next.js and npm symlinks may experience quirks on FAT32 if not handled properly.

### Strategic Mitigation:
- **Dependency Caching & Temp Files:** Direct npm cache, Python virtual environment caches, and heavy temporary build artifacts to local system temp when possible or optimize package installs using flat module layouts.
- **Backup Segmentation:** Database backup archives (`.sql.gz`) must be structured with split rotation (max 1 GB per chunk) to stay well under the FAT32 4 GB limit.
- **Transaction Flush:** Ensure all database write streams and file operations call explicit sync/flush on completion.
- **Workspace Confinement:** All source code, documents, and test harnesses remain strictly inside `E:\NEXORA_AI` as mandated by Rule 1.

---

## ADR-002: Docker Daemon Status & Sandboxed Code Execution Architecture

### Status: ACCEPTED WITH DUAL-TIER EXECUTION PIPELINE

### Context:
Inspection of the execution environment revealed:
- `docker.exe` CLI is installed (`v29.9.3`).
- However, the Docker daemon connection returned: `failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine`. Docker Desktop and its WSL2 distro `docker-desktop` are currently in `Stopped` state.
- Rule 14 mandates: *"Do not use unsafe code execution methods."*
- Primary objective mandates: *"Secure coding execution platform. Dedicated isolated execution worker. No direct host execution of submitted code. Resource limits, timeouts, network restrictions, process isolation."*

### Architectural Resolution:
1. **Never rely solely on a live Docker daemon for local development and test automation.** If Docker Desktop is stopped or unavailable, the system must not be paralyzed.
2. **Dual-Tier Isolated Execution Architecture:**
   - **Tier 1 (Production Containerized Worker):** Docker / container-based execution worker configured via `infrastructure/docker-compose.yml` for production deployments where Docker daemon is active.
   - **Tier 2 (Process-Isolated Subprocess Sandbox):** A standalone worker utilizing Python `subprocess` with:
     - Non-root/unprivileged execution context.
     - Strict execution timeouts (3 seconds for Python, 5 seconds for Java/C++).
     - Memory limits enforced via OS job objects or resource limits.
     - Zero network access (isolated environment variables, blocked network sockets).
     - Strict directory jail restricting read/write strictly to a temporary scratch directory purged after every execution.
     - Input/output sanitization with length caps (max 64 KB stdout/stderr).

---

## ADR-003: Multi-Database Strategy (PostgreSQL Production & SQLite Local Test Isolation)

### Status: ACCEPTED

### Context:
Section 4 mandates PostgreSQL as the primary relational database, and SQLite strictly for isolated local development and automated testing.

### Architectural Resolution:
- Use SQLAlchemy 2.0 async engine with an abstraction layer (`DATABASE_URL` dynamic protocol detection: `postgresql+asyncpg://` vs `sqlite+aiosqlite://`).
- In automated test runs and local sandbox environments without live PostgreSQL services running, the test harness automatically routes to an in-memory or isolated local SQLite database (`sqlite+aiosqlite:///test_nexora.db`).
- Schema migrations are managed uniformly via Alembic, supporting cross-dialect generation while maintaining referential integrity and index definitions.

---

## ADR-004: Unified AI Engine Provider Abstraction & Offline Fallback

### Status: ACCEPTED

### Context:
Rule 7 prohibits paid APIs without approval. Section 6 (Module A) mandates a provider-independent architecture with local fallback capabilities.

### Architectural Resolution:
- Create `BaseAIProvider` abstract interface.
- Implement providers:
  1. `GeminiAIProvider` (Free tier Google Gemini API with API key from environment).
  2. `LocalDeterministicFallbackProvider` (Rule-based heuristic and algorithmic template engine that activates automatically when offline or when no API key is supplied).
  3. `MockAIProvider` (Deterministic provider for unit tests and CI pipelines).
- Guarantee: The system never crashes or hangs when external AI networks fail.

---

## ADR-005: Security, RBAC & IDOR Mitigation Architecture

### Status: ACCEPTED

### Architectural Resolution:
- Centralized JWT verification using dual-token strategy: short-lived access tokens (15 minutes) and HTTP-only, secure, same-site refresh tokens (7 days).
- Role-Based Access Control (RBAC) enforced via FastAPI endpoint dependencies (`require_roles([Role.STUDENT])`, `require_roles([Role.ADMIN])`, `require_roles([Role.PLACEMENT_CELL])`).
- Inherent IDOR Protection: Every database query accessing user data (resumes, test attempts, submissions, chat threads) explicitly binds `user_id == current_user.id` or validates administrative ownership before executing mutations or reads.
