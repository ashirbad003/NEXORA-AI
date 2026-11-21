# NEXORA AI — PHASE 6 ACCEPTANCE CRITERIA

**Date:** 2026-11-21  
**Workspace:** `E:\NEXORA_AI`  
**Milestone:** Phase 6 (Unified AI Brain & AI Career Copilot)  
**Standard:** Strict Zero-Defect Pass/Fail Gates  

---

## 1. Feature-by-Feature Acceptance Criteria (FEAT-001 to FEAT-040)

| Feature ID | Feature Name | Mandatory Acceptance Criteria |
| :--- | :--- | :--- |
| **FEAT-001** | Central AI Provider Abstraction Interface | `get_ai_provider()` dynamically returns Gemini, Local, or Mock based on config; identical interface across all providers. |
| **FEAT-002** | Student Context Aggregator | Gathers student's degree, target role, completed topics, coding stats, and quiz scores into a single structured dictionary in < 100ms. |
| **FEAT-003** | Deterministic Offline Fallback Engine | If Gemini API key is missing or network times out, provider automatically falls back to local rule-based engine; returns status 200 with `is_fallback=True`. |
| **FEAT-004** | Token & Cost Telemetry Tracker | Every AI request logs token counts and execution duration; accessible via admin or telemetry service. |
| **FEAT-005** | AI Prompt Safety & Sanitization Filter | Blocks prompt injection phrases (e.g. "ignore previous instructions", "reveal system prompt") and returns safe error message. |
| **FEAT-006** | AI Recommendation Explainability Engine | AI recommendations include an `explainability_rationale` explaining why a specific task or topic was prioritized. |
| **FEAT-007** | Context Window Optimization | Truncates or summarizes chat history if tokens exceed model limit, preserving recent 5 turns and system instructions. |
| **FEAT-008** | Model Response Schema Validator | Structured output endpoints validate that JSON matches defined Pydantic schema; raises validation error on malformed outputs. |
| **FEAT-009** | Personalized AI Persona Manager | Allows student to select AI persona ("Strict Interviewer", "Friendly Mentor", "Technical Architect"); prompts adapt tone accordingly. |
| **FEAT-010** | Multi-turn Conversation Persistence | Messages persisted in `copilot_messages` table; reloading `/copilot` loads previous conversation turns in order. |
| **FEAT-011** | AI Latency & Timeout Guardian | Requests taking > 10.0 seconds are cancelled and fall back to local offline response without hanging thread. |
| **FEAT-012** | Skill Gap Vector Matcher | Compares student's mastered skills against target role matrix; outputs missing priority skills and gap percentage. |
| **FEAT-013** | Realtime AI Streaming Support | Endpoint supports SSE token streaming or chunked transmission with minimal time-to-first-token. |
| **FEAT-014** | AI Output Confidence Score Estimator | AI responses include a confidence estimate (0.0–1.0) based on context match density. |
| **FEAT-015** | Automated AI Feedback Logging | Endpoint `POST /copilot/feedback` records user rating (thumbs up/down) and optional comment. |
| **FEAT-016** | Career Readiness Index Calculator | Computes composite score (0–100) reflecting curriculum completion, coding scores, and consistency. |
| **FEAT-017** | AI Rate Limiter & Quota Gate | Enforces 50 queries/day per student; returns 429 Too Many Requests when quota exceeded. |
| **FEAT-018** | Multi-Language Explanation Translator | Explanations can be generated or rendered in Hindi/Hinglish upon request. |
| **FEAT-019** | Weakness Remediation Plan Generator | Analyzes recent failed questions/submissions and generates a focused 7-day study regimen. |
| **FEAT-020** | AI Knowledge Graph Concept Linker | Links AI responses to existing curriculum concept slugs (e.g., `/learn/binary-search`). |
| **FEAT-021** | Personalized Career Path Selector | Student can select track (Frontend, Backend, SDE, Data Engineering, DevOps) and save preference. |
| **FEAT-022** | Dynamic 90-Day Placement Roadmap | Generates 12 weekly milestones tailored to target track, target companies, and current skill level. |
| **FEAT-023** | Daily Sprints & Actionable Goals | Decomposes current week's milestone into daily bite-sized tasks; tasks can be toggled completed. |
| **FEAT-024** | Target Company Preparation Matrix | Customizes roadmap with specific company interview focus areas (e.g. Google graphs, Amazon LP). |
| **FEAT-025** | Skill Benchmark Against Industry Standards | Visualizes student's current proficiency vs tier-1 expectations across 6 skill dimensions. |
| **FEAT-026** | Internship Readiness Evaluator | Provides specific readiness percentage and missing prerequisites for summer internships. |
| **FEAT-027** | Weekly Progress Digest Generator | Summarizes weekly hours, completed tasks, solved problems, and score delta. |
| **FEAT-028** | Study Habit & Velocity Tracker | Calculates current study streak and weekly task velocity (tasks completed / week). |
| **FEAT-029** | Smart Project Recommendation Engine | Recommends 3 industry-grade project ideas matching target role with required tech stack. |
| **FEAT-030** | Peer Rank & Cohort Comparison | Displays student's percentile relative to anonymous peer cohort in same department/year. |
| **FEAT-031** | Career Milestone Badge System | Unlocks visual badges upon completing 25%, 50%, 75%, and 100% of roadmap milestones. |
| **FEAT-032** | AI Mentor Direct Q&A Console | Responsive interactive chat console embedded in `/copilot` with markdown code blocks and action chips. |
| **FEAT-033** | Resume-Driven Roadmap Adjustment | Re-analyzing skills recalculates roadmap milestones without wiping completed tasks. |
| **FEAT-034** | Interview Timeline Countdown | Displays days remaining to college placement season or configured target interview date. |
| **FEAT-035** | Burnout & Fatigue Warning Detector | Flags warning if student logs > 8 hours daily for 5 consecutive days or fails > 10 coding attempts in 2 hours. |
| **FEAT-036** | Target Salary & Compensation Insights | Displays realistic entry-level CTC ranges for target role across Indian and global tech markets. |
| **FEAT-037** | Certification Recommendation Finder | Suggests verified AWS, GCP, CKA, or Azure certifications pertinent to selected track. |
| **FEAT-038** | Campus Placement Eligibility Checker | Validates student's CGPA, active backlogs, and attendance against standard placement criteria (e.g., 60%+ throughout). |
| **FEAT-039** | Daily Tech Trivia & Micro-Quiz | Serves 1 daily multiple-choice interview trivia question; records streak. |
| **FEAT-040** | Study Group Matcher | Suggests peers studying the same target track or companies for peer preparation. |

---

## 2. Release & Verification Quality Gates

1. **Backend Unit & Integration Tests:** 100% pass rate; zero failed, zero skipped.
2. **Frontend TypeScript Check:** `npm --prefix frontend run typecheck` produces 0 errors.
3. **Frontend Production Build:** `npm --prefix frontend run build` succeeds; `/copilot` route prerendered.
4. **Feature Registry Validation:** `python scripts/validate_feature_registry.py` passes 346/346.
5. **Phase 0–5 Regression:** All 69 existing backend tests, 20 container tests, and 7 arena tests continue passing.
