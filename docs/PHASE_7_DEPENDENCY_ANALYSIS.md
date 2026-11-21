# NEXORA AI — PHASE 7 DEPENDENCY ANALYSIS
## Upstream Integrations & Cross-Module Dependencies

**Workspace:** `E:\NEXORA_AI`
**Git Baseline Checkpoint:** `424e8ff647c8456bf2152c15321e16fbfebac70e`
**Status:** **VERIFIED**

---

## 1. Upstream Phase 0–6 Dependencies

Phase 7 features depend directly on infrastructure, authentication, AI brain capabilities, and data models delivered in earlier phases:

| Dependency Area | Required Phase 0–6 Components | Impact on Phase 7 Features |
| :--- | :--- | :--- |
| **Authentication & RBAC** | `FEAT-311` (JWT Auth), `FEAT-313` (RBAC Guards), `User`, `Role` | Protects assessment endpoints, enforces student attempt isolation, grants admin question bank CRUD (`FEAT-058`, `FEAT-122`). |
| **Student Context Aggregator** | `FEAT-002` (`context_aggregator.py`), `StudentProfile` | Injects student background, CGPA, target roles, and historical weaknesses into mock interview setup (`FEAT-109`, `FEAT-121`). |
| **Unified AI Brain** | `FEAT-001` (AI Provider Abstraction), `FEAT-003` (Local Fallback), `FEAT-004` (Telemetry), `FEAT-005` (Prompt Safety), `FEAT-008` (Schema Validator) | Powers AI Mock Interview Studio (`FEAT-103`), STAR scoring (`FEAT-111`), follow-up question generation (`FEAT-110`), and blunder analysis (`FEAT-115`). |
| **Realtime AI Streaming** | `FEAT-013` (`stream_response` async iterator, `/chat/stream` SSE) | Enables low-latency streaming of interviewer voice transcripts and interview dialogue in web UI. |
| **Coding Sandbox** | Phase 5 Sandbox worker (`sandbox/worker.py`), Docker Alpine isolated containers | Powers coding questions in multi-section mock drives (`FEAT-047`, `FEAT-062`). |
| **Database Architecture** | SQLAlchemy 2.0 Async engine, Alembic migrations, PostgreSQL 17 | Foundation for Phase 7 tables (`assessments`, `questions`, `attempts`, `mock_interviews`, `turns`). |

---

## 2. Downstream Module Handoffs

Phase 7 also emits data critical for future phases:

- **Module H (Smart Revision & SM-2, Phase 10):** `FEAT-055` extracts weak topic tags from failed assessment questions to generate spaced-repetition flashcards and mistake notebook entries.
- **Module M (Placement Cell, Phase 9):** `FEAT-048` diagnostic scorecards and `FEAT-117` interview readiness indices determine student eligibility and shortlisting criteria for on-campus drives.
- **Module B (AI Career Copilot, Phase 6):** Assessment percentiles and mock interview scores feed the Career Readiness Index (`FEAT-016`) and 90-day roadmap milestone completions.

---

## 3. External & Browser API Dependencies

| Component | Technology | Free / Self-Contained | Fallback Strategy |
| :--- | :--- | :--- | :--- |
| **Speech-to-Text (`FEAT-104`)** | Browser Web Speech API (`webkitSpeechRecognition`) | 100% Free / Native | Fallback to Text-Based Mode (`FEAT-106`) if browser denies mic permission or lacks speech API support. |
| **Speech Synthesis (`FEAT-105`)** | Browser Web Speech Synthesis (`window.speechSynthesis`) | 100% Free / Native | Fallback to silent text display with audio toggle. |
| **Anti-Cheating Detection (`FEAT-053`)** | Browser `window.onblur`, `document.visibilitychange` | 100% Free / Native | In-memory count with warning modals; logged with attempt state. |
| **Auto-Save (`FEAT-042`)** | Client periodic debounce / 5s heartbeat + `onbeforeunload` | 100% Free / Native | LocalStorage sync + async backend persist. |
| **System Design Whiteboard (`FEAT-120`)** | HTML5 `<canvas>` / SVG interactive drawing engine | 100% Free / Self-contained | SVG primitive toolbox (boxes, arrows, databases, microservices) rendered on client. |
| **AI LLM Inference (`FEAT-103`)** | Gemini API (`gemini-2.5-flash`) / Local Deterministic Engine | Free tier + Offline Fallback | Zero hard dependency on paid APIs; deterministic local generator runs offline. |
