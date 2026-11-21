# NEXORA AI — PHASE 7 IMPLEMENTATION ROADMAP
## Sequential Engineering & Dependency-Aware Execution Plan

**Workspace:** `E:\NEXORA_AI`
**Target Scope:** `FEAT-041` to `FEAT-062` (Assessment Intelligence) & `FEAT-103` to `FEAT-122` (Interview Intelligence)
**Total Features:** 42
**Status:** **PLANNING BASELINE (WAITING FOR EXPLICIT AUTHORIZATION)**

---

## 1. Phased Stage Breakdown

The 42 features are partitioned into four dependency-aware implementation stages:

```
Stage 1: Assessment Database & Core Test Engine (FEAT-041 to FEAT-047, FEAT-058 to FEAT-060)
         │
         ▼
Stage 2: Assessment Diagnostics, Proctoring & Intelligence (FEAT-048 to FEAT-057, FEAT-061, FEAT-062)
         │
         ▼
Stage 3: AI Mock Interview Studio Core & Voice Engine (FEAT-103 to FEAT-110, FEAT-119, FEAT-122)
         │
         ▼
Stage 4: Interview Diagnostics, STAR Scoring & Whiteboard (FEAT-111 to FEAT-118, FEAT-120, FEAT-121)
```

---

### Stage 1: Assessment Database & Core Test Engine (10 Features)
- **Features:** `FEAT-041`, `FEAT-042`, `FEAT-043`, `FEAT-044`, `FEAT-045`, `FEAT-046`, `FEAT-047`, `FEAT-058`, `FEAT-059`, `FEAT-060`.
- **Database Tasks:**
  - Create SQLAlchemy models: `AssessmentTest`, `AssessmentQuestion`, `AssessmentAttempt`, `AssessmentAnswer`.
  - Author and apply Alembic forward migration.
- **Backend Tasks:**
  - Implement `backend/app/services/assessment_service.py` for attempt creation, answer auto-saving, countdown timer synchronization, question shuffling, and negative marking.
  - Implement `backend/app/api/assessments.py` endpoints: `GET /tests`, `POST /tests/{id}/start`, `PUT /attempts/{id}/save`, `POST /attempts/{id}/submit`.
  - Implement Admin Question Bank CRUD & CSV importer (`FEAT-058`, `FEAT-059`).
- **Frontend Tasks:**
  - Build `frontend/src/app/assessments/page.tsx` test directory and test details modal.
  - Build `frontend/src/app/assessments/[id]/take/page.tsx` exam interface with synchronized timer, auto-save heartbeat, question palette, review flagger, and sectional navigation.

---

### Stage 2: Assessment Diagnostics, Proctoring & Intelligence (12 Features)
- **Features:** `FEAT-048`, `FEAT-049`, `FEAT-050`, `FEAT-051`, `FEAT-052`, `FEAT-053`, `FEAT-054`, `FEAT-055`, `FEAT-056`, `FEAT-057`, `FEAT-061`, `FEAT-062`.
- **Backend Tasks:**
  - Implement diagnostic scoring service (accuracy, speed, percentile calculation).
  - Implement weak area tag extraction (`FEAT-055`) for downstream Module H handoff.
  - Implement dynamic adaptive quiz generation and company test templates (TCS NQT, Infosys, Amazon).
  - Implement question reporting & feedback API (`FEAT-057`).
  - Implement PDF/HTML certificate generator (`FEAT-061`).
- **Frontend Tasks:**
  - Build anti-cheating window blur / tab-switch tracker modal (`FEAT-053`).
  - Build post-test diagnostic scorecard page `frontend/src/app/assessments/[id]/scorecard/page.tsx` with radar charts, solution explanation viewer, and historical score progression.
  - Build public assessment leaderboard tab (`FEAT-056`).

---

### Stage 3: AI Mock Interview Studio Core & Voice Engine (10 Features)
- **Features:** `FEAT-103`, `FEAT-104`, `FEAT-105`, `FEAT-106`, `FEAT-107`, `FEAT-108`, `FEAT-109`, `FEAT-110`, `FEAT-119`, `FEAT-122`.
- **Database Tasks:**
  - Create SQLAlchemy models: `InterviewSession`, `InterviewTurn`, `InterviewFeedback`.
  - Author and apply Alembic forward migration.
- **Backend Tasks:**
  - Implement `backend/app/services/interview_service.py` using Unified AI Brain provider abstraction (`generate_response` and `stream_response`).
  - Add persona routing for Technical Deep-Dive, HR/Behavioral, and Company-Specific interview tracks (Google, Amazon, TCS).
  - Implement dynamic contextual follow-up question generation (`FEAT-110`).
  - Seed behavioral question bank with 200+ exemplary STAR answers (`FEAT-119`).
- **Frontend Tasks:**
  - Build `frontend/src/app/interview/page.tsx` studio launcher with track and persona selector.
  - Build `frontend/src/app/interview/session/page.tsx` interactive simulation studio.
  - Implement Web Speech API integration (`webkitSpeechRecognition`) for voice input with automatic fallback to text mode (`FEAT-104`, `FEAT-106`).
  - Implement browser speech synthesis (`window.speechSynthesis`) for vocalized interviewer responses (`FEAT-105`).

---

### Stage 4: Interview Diagnostics, STAR Scoring & Whiteboard (10 Features)
- **Features:** `FEAT-111`, `FEAT-112`, `FEAT-113`, `FEAT-114`, `FEAT-115`, `FEAT-116`, `FEAT-117`, `FEAT-118`, `FEAT-120`, `FEAT-121`.
- **Backend Tasks:**
  - Implement STAR methodology rubric scorer (Situation, Task, Action, Result) (`FEAT-111`).
  - Implement communication tone, clarity, and filler-word density analyzer (`FEAT-112`).
  - Implement answer relevance and technical accuracy evaluator (`FEAT-113`).
  - Implement holistic Interview Readiness Index (0–100) and personalized improvement plan generator (`FEAT-116`, `FEAT-117`).
  - Implement resume-based question generator parsing `StudentProfile` projects and skills (`FEAT-121`).
- **Frontend Tasks:**
  - Build interactive System Design Whiteboard canvas (`FEAT-120`) supporting architecture block diagrams.
  - Build timer and pacing coach visual indicator (`FEAT-118`).
  - Build post-interview feedback and playback review studio (`FEAT-114`, `FEAT-115`).
