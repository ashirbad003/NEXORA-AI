# NEXORA AI — PHASE 7 ACCEPTANCE CRITERIA
## Quality Gates, Assertion Criteria & Test Specifications

**Workspace:** `E:\NEXORA_AI`
**Target Scope:** `FEAT-041` to `FEAT-062` & `FEAT-103` to `FEAT-122` (42 Features)
**Status:** **MANDATORY ACCEPTANCE SPECIFICATION**

---

## 1. Module C: Assessment Intelligence Acceptance Criteria

1. **Timed Expiry Enforcement (`FEAT-041`):**
   - Given a test with `duration_minutes = 30`, when the countdown reaches 00:00, the client must trigger automatic submission and the backend must reject answers submitted after expiration with HTTP 400.
2. **Auto-Save Resilience (`FEAT-042`, `FEAT-043`):**
   - Selected option must be saved asynchronously within 5 seconds without blocking UI.
   - If a student reloads or closes the tab, returning to the test must restore their exact saved answers and the remaining time minus elapsed time.
3. **Randomization & Shuffling (`FEAT-044`):**
   - Two students taking the same test must receive different question ordering and option permutations seeded by their unique `attempt_id`.
4. **Scoring & Negative Marking (`FEAT-045`):**
   - Correct answers award positive marks (e.g., +1.0); incorrect answers deduct configured penalty (e.g., -0.25); unattempted questions award 0.0 marks.
5. **Anti-Cheating Window Blur (`FEAT-053`):**
   - Switching browser tabs or minimizing the window triggers a warning modal and increments `blur_count`. If `blur_count` exceeds test threshold (e.g. 3), test is flagged.
6. **Diagnostic Scorecard (`FEAT-048`, `FEAT-049`):**
   - Scorecard displays total score, accuracy percentage, time spent per section, correct/incorrect breakdowns, and comprehensive explanations for every question.
7. **Weak Area Extractor (`FEAT-055`):**
   - Tags associated with incorrectly answered questions are persisted into the student's weakness registry for downstream Module H flashcards.

---

## 2. Module F: Interview Intelligence Acceptance Criteria

1. **Voice & Text Duality (`FEAT-104`, `FEAT-105`, `FEAT-106`):**
   - Student speech input must be transcribed in real time via Web Speech API.
   - Interviewer responses must be vocalized via speech synthesis.
   - When microphone permissions are denied or unsupported, the studio must seamlessly operate in text chat mode with zero functionality loss.
2. **Dynamic Contextual Follow-ups (`FEAT-110`):**
   - Given a vague or shallow technical answer, the AI interviewer must ask a targeted follow-up digging deeper into the specific trade-offs mentioned.
3. **STAR Methodology Scorer (`FEAT-111`):**
   - Behavioral responses must be graded across Situation, Task, Action, and Result dimensions on a 1–5 scale with actionable improvement notes.
4. **Communication Tone & Clarity Analyzer (`FEAT-112`):**
   - Responses must be evaluated for filler word frequency ("um", "like", "you know"), clarity, vocabulary level, and professional cadence.
5. **Whiteboard Canvas (`FEAT-120`):**
   - In System Design mode, an interactive diagramming canvas allows drawing boxes, arrows, and architecture entities alongside the interview dialogue.
6. **Fail-Closed & Offline Resilience (`FEAT-003`):**
   - If the Gemini API key is missing or external network is unavailable, mock interviews must execute using the deterministic local offline fallback engine with full rubric scoring.

---

## 3. Mandatory Quality Gates

- `pytest tests/ -q` passes 100% across all phases (including new Phase 7 tests).
- `python -m unittest sandbox.tests.test_live_container_execution -v` passes 20/20 container isolation tests.
- `npm --prefix frontend run typecheck` passes with zero errors.
- `npm --prefix frontend run build` compiles all routes successfully.
- `python scripts/validate_feature_registry.py` verifies 346/346 features.
- Database migration applies forward cleanly and rolls back cleanly without data loss.
