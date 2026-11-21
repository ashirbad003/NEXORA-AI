# NEXORA AI — PHASE 8 RISK & ROLLBACK PLAN
## Operational Safety & Rollback Procedures

**Workspace:** `E:\NEXORA_AI`  
**Phase:** 8

---

## 1. Technical Risks & Mitigations
- **GitHub Rate Limiting:** Public GitHub unauthenticated API allows 60 requests/hr. Mitigation: In-memory/database caching with mock fallback when rate-limited.
- **Resume File Size Exceedance:** PDF uploads could overload memory. Mitigation: Strict 5MB request body limit and direct text-based parsing.

## 2. Rollback Protocol
- Downgrade migration: `alembic downgrade b7fcde829101`.
- Reset git: `git reset --hard b228ea2f9bb2602b8c967e2989d7b7c0a3ffa4b7`.
