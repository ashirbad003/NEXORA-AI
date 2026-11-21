# NEXORA AI — PHASE 6 IMPLEMENTATION ROADMAP

**Date:** 2026-11-21  
**Workspace:** `E:\NEXORA_AI`  
**Repository:** `ashirbad003/NEXORA-AI`  
**Target Milestone:** Phase 6 (Unified AI Brain & AI Career Copilot)  
**Total Canonical Features:** 40 (`FEAT-001` through `FEAT-040`)  

---

## 1. Implementation Strategy & Phased Slices

To maintain zero-defect standards, Phase 6 should be executed in 4 logical stages:

```
Stage 1: AI Brain Engine & Guardrails (FEAT-001 to FEAT-011, FEAT-013 to FEAT-015, FEAT-017)
Stage 2: Student Context, Vector Matching & Analytics (FEAT-002, FEAT-012, FEAT-016, FEAT-018 to FEAT-020)
Stage 3: Database Models, Migrations & Copilot Backend Services (FEAT-021 to FEAT-031, FEAT-033 to FEAT-040)
Stage 4: Frontend UI, Interactive Copilot Console & End-to-End Testing (FEAT-032, Full UI & Regression Gates)
```

---

## 2. Stage-by-Stage Task Breakdown

### Stage 1: AI Brain Core, Safety & Telemetry
1. **Gemini Provider Integration (`FEAT-001`):** Implement `ai_engine/providers/gemini.py` utilizing the official SDK / REST client with graceful error trapping.
2. **Deterministic Fallback Enhancement (`FEAT-003`):** Expand `LocalDeterministicFallbackProvider` to generate high-fidelity placement roadmaps and technical mentorship offline.
3. **Prompt Safety & Sanitization (`FEAT-005`):** Implement `ai_engine/guardrails/sanitizer.py` filtering prompt injection patterns, secret extraction prompts, and jailbreaks.
4. **Schema Validator (`FEAT-008`):** Implement `ai_engine/guardrails/schema_validator.py` enforcing structured JSON responses via Pydantic models.
5. **Latency Guardian (`FEAT-011`):** Wrap AI invocations with `asyncio.wait_for(..., timeout=10.0)`.
6. **Token Telemetry Tracker (`FEAT-004`):** Log prompt tokens, completion tokens, model name, latency, and estimated cost in `ai_engine/telemetry/`.
7. **Rate Limiting Quota Gate (`FEAT-017`):** Enforce 50 queries/day per user.

### Stage 2: Context Aggregation & Skill Intelligence
1. **Student Context Aggregator (`FEAT-002`):** Aggregate GPA, mastered topics, coding submission pass rates, and weak tags into a single rich prompt context.
2. **Skill Gap Vector Matcher (`FEAT-012`):** Match student skill vectors against target company tech stacks using deterministic cosine distance.
3. **Career Readiness Index (`FEAT-016`):** Combine learning progress (30%), coding submissions (40%), and profile completeness (30%) into a 0–100 score.
4. **Weakness Remediation Generator (`FEAT-019`):** Identify lowest-scoring quiz/coding categories and formulate a 7-day catch-up schedule.
5. **Multi-Language Translator (`FEAT-018`):** Support explanations in Hindi, Hinglish, and English.

### Stage 3: Copilot Database Schema & Backend API
1. **Database Models & Alembic Migration:**
   - Create `backend/app/models/copilot.py` with `CopilotCareerPath`, `CopilotRoadmap`, `CopilotSprintTask`, `CopilotConversation`, `CopilotMessage`.
   - Generate and apply Alembic migration `a1b2c3d4e5f6_phase_6_copilot_tables.py`.
2. **Copilot Service (`backend/app/services/copilot_service.py`):**
   - Implement roadmap generation algorithm (`FEAT-022`), daily sprint decomposition (`FEAT-023`), company matrix tailoring (`FEAT-024`), milestone badge awarding (`FEAT-031`), and habit tracking (`FEAT-028`).
3. **Copilot API Router (`backend/app/api/copilot.py`):**
   - Endpoints:
     - `GET /api/v1/copilot/roadmap`: fetch current roadmap.
     - `POST /api/v1/copilot/roadmap/generate`: generate/regenerate 90-day plan.
     - `GET /api/v1/copilot/sprints/today`: get daily sprint tasks.
     - `PATCH /api/v1/copilot/sprints/{task_id}`: toggle task completion.
     - `POST /api/v1/copilot/chat`: multi-turn Q&A with AI mentor.
     - `GET /api/v1/copilot/chat/history`: retrieve conversation messages.
     - `GET /api/v1/copilot/insights`: salary ranges, benchmarks, and burnout warnings.

### Stage 4: Frontend Copilot Console & End-to-End Validation
1. **Frontend Copilot Page (`frontend/src/app/copilot/page.tsx`):**
   - Tab 1: **90-Day Placement Roadmap** (Week-by-week timeline, status pills, milestone badges).
   - Tab 2: **Today's Actionable Sprint** (Interactive checklist, progress bar, daily trivia).
   - Tab 3: **Target Company Readiness Matrix** (Skill gaps radar, company benchmarks).
   - Tab 4: **AI Mentor Q&A Console** (Multi-turn chat, markdown rendering, prompt suggestions).
2. **Navbar Integration:** Add "Career Copilot" navigation link.
3. **Testing Suite:**
   - Unit tests: `tests/unit/test_phase_6_ai_brain.py` (Provider switching, fallback, sanitization).
   - Integration tests: `tests/integration/test_phase_6_copilot.py` (API endpoints, persistence, RBAC).
   - TypeScript check & Production build validation.

---

## 3. Complexity and Risk Assessment

| Stage | Estimated Complexity | Primary Risk | Mitigation |
| :--- | :--- | :--- | :--- |
| **Stage 1 (Brain Core)** | Medium | External API network latency / outage | Strict fallback to deterministic offline engine |
| **Stage 2 (Context & Matching)** | Medium | Incomplete student data on new profiles | Safe defaults and cold-start fallback profiles |
| **Stage 3 (DB & Backend)** | High | Complex relational hierarchy (roadmaps -> weeks -> sprints) | Clean foreign keys with CASCADE deletes; validated Alembic migration |
| **Stage 4 (Frontend UI)** | Medium | Heavy multi-tab UI performance | Modular components with React state caching |
