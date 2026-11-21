# NEXORA AI — PHASE 10 ACCEPTANCE CRITERIA & QUALITY GATES

**Workspace:** `E:\NEXORA_AI`  
**Phase:** 10 (Smart Revision, Peer Learning & Notifications)  
**Verification Policy:** Zero Flakiness, Zero Test Weakening, 100% Deterministic Evidence  

---

## 1. Feature-Level Acceptance Criteria

### Module H: Smart Revision & Spaced Repetition (`FEAT-145`..`FEAT-162`)
- **`AC-REV-01` (SM-2 Calculation):**
  - Rating 0–2 (Again/Blackout): Resets repetition count to 0, interval to 1 day; EF remains unchanged.
  - Rating 3 (Hard): Repetition increments; interval calculated using EF; EF decreases by 0.14.
  - Rating 4 (Good): Repetition increments; interval calculated using EF; EF remains stable.
  - Rating 5 (Easy): Repetition increments; interval calculated with bonus; EF increases by 0.10.
  - Minimum EF boundary clamped at 1.30.
- **`AC-REV-02` (Weak-Topic Ingestion):**
  - Failed coding submissions (`status != 'ACCEPTED'`) automatically populate the mistake notebook with problem title, error output, and topic tags.
- **`AC-REV-03` (Daily Target Counter):**
  - Returns count of cards where `next_review_at <= now()` with sub-second query latency.

### Module O: Peer Learning & Community (`FEAT-277`..`FEAT-292`)
- **`AC-PEER-01` (Contextual Doubt Binding):**
  - Thread created with `context_type='CODING_PROBLEM'` and `context_id` links directly to the target problem.
- **`AC-PEER-02` (Karma & Reputation Integrity):**
  - Upvote awards +5 karma; marked as accepted answer awards +15 karma.
  - Duplicate upvotes by the same user are rejected with HTTP 409.
- **`AC-PEER-03` (Toxic Moderation Heuristics):**
  - Posts containing prohibited profanity, slur, or spam patterns are automatically flagged with `status='FLAGGED_MODERATION'` and hidden from public feed.

### Module P: Notification Intelligence (`FEAT-293`..`FEAT-308`)
- **`AC-NOTIF-01` (Preference Filtering):**
  - When user toggles off email or in-app channel for category `COMMUNITY_REPLY`, notifications in that category are not dispatched to that channel.
- **`AC-NOTIF-02` (Drawer Badge Counter):**
  - Unread count reflects `count(is_read=False)` and decrements instantly upon marked read.
- **`AC-NOTIF-03` (Real-Time WebSocket Bus):**
  - User connected to `/api/v1/notifications/ws` receives JSON payload immediately when backend publishes an event.

---

## 2. Mandatory Quality Gates

| Gate ID | Quality Gate Description | Target Requirement | Evaluation Method |
| :---: | :--- | :--- | :--- |
| **QG-01** | **Backend Unit Tests** | 100% Pass across all SM-2 and notification unit tests | `pytest tests/unit/` |
| **QG-02** | **Phase 10 Integration Tests** | Full end-to-end integration verified | `python -m unittest tests.integration.test_phase_10` |
| **QG-03** | **Regression Safety** | Zero regressions across Phases 0–9 backend tests (87+ passed) | `pytest tests/ -q` |
| **QG-04** | **Docker Sandbox Isolation** | 20/20 Live container execution tests passing | `test_live_container_execution.py` |
| **QG-05** | **TypeScript Type Checking** | 0 Type errors | `npm --prefix frontend run typecheck` |
| **QG-06** | **Frontend Production Build** | All routes compiled and optimized | `npm --prefix frontend run build` |
| **QG-07** | **Feature Registry Alignment** | 346/346 canonical features registered and mapped | `python scripts/validate_feature_registry.py` |
| **QG-08** | **Secret & Codename Scan** | 0 Leaks, zero private keys or codename occurrences | Automated regex scan |
| **QG-09** | **Database Migration Health** | Forward-only, reversible, 0 data destruction | Live PostgreSQL migration verification |
