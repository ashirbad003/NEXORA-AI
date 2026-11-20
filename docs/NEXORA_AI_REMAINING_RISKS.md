# NEXORA AI — Remaining Risks & Operational Limitations Report

**Date:** 2026-11-20  
**Workspace:** `E:\NEXORA_AI`  
**Scope:** Technical Debt, Infrastructure Boundaries, Operational Dependencies, and Mitigations

---

## 1. Operational & Technical Risk Matrix

| Risk ID | Category | Description | Severity | Impact | Current Mitigation / Status |
|---|---|---|---|---|---|
| **RISK-01** | Sandbox Security | Untrusted student code could escape if unisolated host subprocesses were enabled. | HIGH | Arbitrary command execution on host. | **Mitigated:** `SANDBOX_MODE="disabled"`. Host execution is fail-closed and strictly blocked until Phase 5 Docker isolation is landed. |
| **RISK-02** | File System Limits | `E:` drive is formatted as FAT32, preventing files larger than 4 GiB. | MEDIUM | Database backups, AI model weights, or large dumps could truncate or fail. | **Mitigated:** Documented in deployment runbook. Large databases and dumps must reside on NTFS volume (`C:`). |
| **RISK-03** | Frontend Build FS | Windows Next.js webpack cache snapshot error on FAT32 drive during build. | LOW | Next.js build might encounter `Unable to snapshot resolve dependencies`. | **Mitigated:** `patch_fs.js` preload hook applied in build command (`$env:NODE_OPTIONS="-r ./patch_fs.js"; npm run build`). |
| **RISK-04** | Synchronous Alembic Driver | Alembic CLI requires synchronous PostgreSQL driver (`psycopg2`) rather than `asyncpg`. | LOW | Migration runner fails if `psycopg2` is not installed or driver string is not translated. | **Mitigated:** `backend/alembic/env.py` automatically adapts URL to `postgresql+psycopg2://`. |
| **RISK-05** | Mobile App Scope | `mobile/` directory contains scaffolding files only (`package.json`, `app.json`). | LOW | Expectation mismatch if users assume React Native app is already built. | **Mitigated:** Clearly documented as scaffolding. Mobile development is explicitly assigned to Phase 11. |
| **RISK-06** | AI Provider Scope | External cloud LLM providers (e.g. Gemini, OpenAI) are abstracted but not configured with live external keys. | LOW | Advanced dynamic generation relies on local deterministic heuristics. | **Mitigated:** `LocalDeterministicProvider` supplies reproducible offline responses without incurring cloud costs or token usage. |

---

## 2. Recommended Action Plan for Phase 4 & Beyond

1. **Phase 4 (Student Dashboard & Learning Hub):**
   - Implement frontend visualization components for DSA topic graphs and roadmap progression.
   - Maintain strict IDOR scoping on all student learning progress APIs.
2. **Phase 5 (Coding Arena Container Worker):**
   - Provision dedicated Linux-based Docker worker daemon (`--network none`, `--memory 128m`, `--cpus 0.5`, `--read-only`).
   - Only switch `SANDBOX_MODE="container_isolated"` after running automated container escape verification tests.
3. **Database Maintenance:**
   - Continue running automated tests exclusively against `nexora_test` to keep `nexora_dev` pristine.
