# NEXORA AI — PHASE 6 DEPENDENCY ANALYSIS

**Date:** 2026-11-21  
**Workspace:** `E:\NEXORA_AI`  
**Repository:** `ashirbad003/NEXORA-AI`  
**Checkpoint:** `aa86aad91c0b350b574b152388cc9140014002df`  

---

## 1. Upstream Dependencies (Phase 0 through Phase 5)

Phase 6 requires existing data, services, and models established in earlier phases:

| Dependency Component | Source Phase | Required Capability for Phase 6 | Status & Evidence |
| :--- | :--- | :--- | :--- |
| **User & Student Models** | Phase 2 | `User`, `StudentProfile` models (`department`, `year_of_study`, `cgpa`, `skills`, `target_role`) | **AVAILABLE & VERIFIED** (`backend/app/models/auth.py`) |
| **Authentication & RBAC** | Phase 2 | JWT token validation, `get_current_active_user`, `require_role(UserRole.STUDENT)` | **AVAILABLE & VERIFIED** (`backend/app/api/deps.py`) |
| **Learning Progress Data** | Phase 4 | `UserTopicProgress`, `UserBookmark`, `PersonalNote`, `UserQuizAttempt` | **AVAILABLE & VERIFIED** (`backend/app/models/learning.py`) |
| **Coding Arena Stats** | Phase 5 | `CodeSubmission`, `StudentCodingStats`, problem history, solved tags | **AVAILABLE & VERIFIED** (`backend/app/models/coding.py`) |
| **Frontend Layout Shell** | Phase 3 | Responsive `Navbar`, `Footer`, `AuthProvider`, Obsidian & Cyber Lime design tokens | **AVAILABLE & VERIFIED** (`frontend/src/`) |
| **Next.js Route Structure** | Phase 1–5 | App Router with TypeScript 5.x, Tailwind CSS, Lucide icons | **AVAILABLE & VERIFIED** (`frontend/src/app/`) |
| **Database Migration Engine** | Phase 2 | Alembic forward-only migration pipeline on PostgreSQL 17 | **AVAILABLE & VERIFIED** (Head: `92c890123def`) |

---

## 2. Cross-Feature Internal Dependencies within Phase 6

Phase 6 features have strict internal sequencing constraints:

```
[FEAT-001: Central AI Provider Abstraction]
    │
    ├──> [FEAT-003: Deterministic Offline Fallback Engine]
    ├──> [FEAT-004: Token & Cost Telemetry]
    ├──> [FEAT-005: Prompt Safety & Sanitization Filter]
    ├──> [FEAT-008: Model Response Schema Validator]
    └──> [FEAT-011: Timeout & Latency Guardian]
            │
            ▼
[FEAT-002: Student Context Aggregator] (reads Phase 2/4/5 tables)
    │
    ├──> [FEAT-012: Skill Gap Vector Matcher]
    ├──> [FEAT-016: Career Readiness Index Calculator]
    │
    ▼
[FEAT-021: Personalized Career Path Selector]
    │
    ▼
[FEAT-022: Dynamic 90-Day Placement Roadmap]
    │
    ├──> [FEAT-023: Daily Sprints & Actionable Goals]
    ├──> [FEAT-024: Target Company Preparation Matrix]
    ├──> [FEAT-025: Skill Benchmark Against Industry Standards]
    ├──> [FEAT-026: Internship Readiness Evaluator]
    ├──> [FEAT-029: Smart Project Recommendation Engine]
    └──> [FEAT-031: Career Milestone Badge System]
            │
            ▼
[FEAT-010: Multi-turn Conversation Persistence]
    │
    ▼
[FEAT-032: AI Mentor Direct Q&A Console]
    │
    ├──> [FEAT-013: Realtime Streaming Support (SSE)]
    ├──> [FEAT-015: Automated AI Feedback Logging]
    └──> [FEAT-017: AI Rate Limiter & Quota Gate]
```

---

## 3. External Service Dependencies & Cost Boundaries

1. **AI Model Provider (Gemini API / Free Tier):**
   - The primary external provider is Google Gemini API (`gemini-1.5-flash` or `gemini-2.0-flash`).
   - Free tier API key support via environment configuration `GEMINI_API_KEY`.
   - **MANDATORY REQUIREMENT:** Zero hard dependencies on paid subscriptions. The system must operate 100% reliably in offline environments using the deterministic local provider (`LocalDeterministicFallbackProvider` in `ai_engine/providers/local.py`).
2. **Embedding & Vector Search:**
   - Skill gap matching (`FEAT-012`) must use local deterministic TF-IDF / cosine keyword vectorization (or scikit-learn / pure Python cosine similarity) to avoid requiring vector database subscriptions (e.g. Pinecone).
3. **Database Requirements:**
   - PostgreSQL 17 locally hosted on port 5432.
   - Zero cloud database dependencies.

---

## 4. Downstream Dependencies (Future Phases 7+)

Phase 6 provides foundational AI capabilities required by subsequent phases:
- **Phase 7 (Mock Interview Intelligence):** Depends on `FEAT-001` (AI Provider), `FEAT-009` (Persona Manager), and `FEAT-010` (Conversation Persistence).
- **Phase 8 (Resume & GitHub Intelligence):** Depends on `FEAT-002` (Student Context Aggregator) and `FEAT-033` (Resume-Driven Roadmap Adjustment).
- **Phase 9 (Placement Cell):** Depends on `FEAT-030` (Cohort Comparison) and `FEAT-038` (Campus Placement Eligibility Checker).
- **Phase 10 (Smart Revision SM-2):** Depends on `FEAT-019` (Weakness Remediation Plan Generator).
