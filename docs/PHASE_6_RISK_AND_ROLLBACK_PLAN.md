# NEXORA AI — PHASE 6 RISK ANALYSIS & ROLLBACK PLAN

**Date:** 2026-11-21  
**Workspace:** `E:\NEXORA_AI`  
**Milestone:** Phase 6 (Unified AI Brain & AI Career Copilot)  

---

## 1. Risk Analysis Matrix

| Risk ID | Risk Description | Likelihood | Impact | Severity | Mitigation Strategy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RSK-01** | External Gemini API outage or rate limits during evaluation | High | High | HIGH | Implement dual-layer fallback: automatically switch to `LocalDeterministicFallbackProvider` with zero user-visible errors. |
| **RSK-02** | Prompt injection or jailbreak attempts in AI mentor console | Medium | High | HIGH | Enforce regex-based prompt sanitization filter (`FEAT-005`) before dispatching prompt to LLM. |
| **RSK-03** | Database migration conflicts with existing tables | Low | High | MEDIUM | Use additive forward-only migrations. All new foreign keys reference `users.id` with `ON DELETE CASCADE`. Never alter existing columns. |
| **RSK-04** | LLM latency causing frontend timeouts or hanging requests | Medium | Medium | MEDIUM | Wrap all AI requests in a 10.0s async timeout guardian (`FEAT-011`). |
| **RSK-05** | Hallucinated or non-parsable structured roadmap JSON | Medium | High | HIGH | Enforce Pydantic schema validator (`FEAT-008`). If JSON validation fails, fallback engine generates deterministic structured roadmap. |
| **RSK-06** | Accidental regression on Phase 0–5 tests | Low | High | HIGH | Execute full test suite (`pytest tests/ -q` and `unittest sandbox/tests/...`) after each stage of Phase 6 implementation. |

---

## 2. Rollback Strategy

If a critical failure occurs during Phase 6 implementation:

### 2.1 Database Rollback Procedure
1. If migration fails during application:
   ```bash
   alembic downgrade 92c890123def
   ```
2. Verify table state in PostgreSQL:
   ```sql
   SELECT table_name FROM information_schema.tables WHERE table_schema='public';
   ```
3. Confirm existing `users`, `coding_problems`, and `learning_*` tables are untouched.

### 2.2 Git Rollback Procedure
1. Certified baseline checkpoint: `aa86aad91c0b350b574b152388cc9140014002df`
2. If uncommitted changes become corrupt:
   ```bash
   git restore .
   git clean -fd
   ```
3. Re-verify baseline with `python -m pytest tests/ -q`.

### 2.3 Feature Flag / Fail-Safe Isolation
- The AI Engine supports `settings.AI_PROVIDER="local"`.
- If external API connectivity fails or key is missing, setting `AI_PROVIDER="local"` enables 100% deterministic offline execution without code rollback.
