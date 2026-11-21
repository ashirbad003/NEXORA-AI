# NEXORA AI — PHASE 7 RISK & ROLLBACK PLAN
## Risk Mitigation, Security Boundaries & Disaster Recovery

**Workspace:** `E:\NEXORA_AI`
**Scope:** Phase 7 Implementation Protection
**Status:** **OPERATIONAL SAFETY SPECIFICATION**

---

## 1. Technical & Architecture Risks

| Risk Identifier | Risk Description | Severity | Mitigation Strategy |
| :--- | :--- | :---: | :--- |
| **RISK-P7-01** | Client Web Speech API browser incompatibility or permission denials | Medium | Full text-mode fallback (`FEAT-106`) is built into the primary interview loop; automatic feature detection switches modes without errors. |
| **RISK-P7-02** | Test timer drift between client JavaScript clock and server UTC time | High | Server maintains authoritative `start_time` and `duration_minutes`. Client timer is purely visual; server enforces strict submission deadline upon POST. |
| **RISK-P7-03** | High concurrency auto-save contention on database during bulk tests | Medium | Debounced 5-second interval per client; lightweight single-row upserts targeting `assessment_answers` indexed by `(attempt_id, question_id)`. |
| **RISK-P7-04** | AI hallucination or uncalibrated scoring during mock interviews | Medium | Pydantic strict response schema validation (`FEAT-008`); bounded numeric rubric scale (1–5) with deterministic local fallback formulas. |
| **RISK-P7-05** | IDOR vulnerability on test attempts or interview playback | High | Enforce row-level ownership: `attempt.student_id == current_user.id` on all attempt retrieval, answer saving, and submission endpoints. |
| **RISK-P7-06** | Database migration failure or conflict with Phase 0–6 tables | High | Alembic migrations written as isolated additive models; schema changes tested against clean SQLite test runner and live PostgreSQL instance. |

---

## 2. Rollback Protocol

If Phase 7 implementation encounters unresolvable defects or breaks Phase 0–6 regressions:

### Step 1: Database Migration Downgrade
```bash
cd backend
alembic downgrade a3ebe19fb261
```
*(Reverts all Phase 7 tables, restoring PostgreSQL schema back to Phase 6 head `a3ebe19fb261` with 22 public tables preserved).*

### Step 2: Code Rollback
```bash
git checkout main
git reset --hard 424e8ff647c8456bf2152c15321e16fbfebac70e
git clean -fd
```
*(Restores codebase directly to the certified Phase 6 GitHub baseline).*

### Step 3: Verification After Rollback
```bash
pytest tests/ -q
python -m unittest sandbox.tests.test_live_container_execution -v
npm --prefix frontend run typecheck
python scripts/validate_feature_registry.py
```
*(Verifies 100% test passing and zero residual issues).*
