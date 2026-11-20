# NEXORA AI: Comprehensive System Architecture & Engineering Blueprint

## 1. Architectural Philosophy
NEXORA AI is built as a high-cohesion, low-coupling ecosystem where all applications (Web, Mobile, Admin, Placement Portal) communicate through a unified backend and adhere to strict security, role-based authorization, and real-time synchronization principles.

```
                    ┌────────────────────────────────────────────────────────┐
                    │               CLIENT TIERS                             │
                    │  ┌──────────────────────┐    ┌──────────────────────┐  │
                    │  │ Next.js Web App      │    │ Android (React Native│  │
                    │  │ (App Router + PWA)   │    │ / Expo Mobile App)   │  │
                    │  └──────────┬───────────┘    └──────────┬───────────┘  │
                    └─────────────┼───────────────────────────┼──────────────┘
                                  │ HTTPS / WSS               │ HTTPS / WSS
                                  ▼                           ▼
                    ┌────────────────────────────────────────────────────────┐
                    │            API GATEWAY & REVERSE PROXY                 │
                    │  (Nginx / Traefik / FastAPI Middleware Gatekeeper)      │
                    │  - Rate Limiting, CORS, Security Headers, SSL/TLS      │
                    └─────────────────────────────┬──────────────────────────┘
                                                  ▼
                    ┌────────────────────────────────────────────────────────┐
                    │               UNIFIED BACKEND ENGINE                   │
                    │                    (FastAPI Core)                      │
                    │  ┌──────────────────────────────────────────────────┐  │
                    │  │ Auth & RBAC (STUDENT, ADMIN, PLACEMENT_CELL)     │  │
                    │  ├──────────────────────────────────────────────────┤  │
                    │  │ Core Services: Student, Assessment, Placement    │  │
                    │  ├──────────────────────────────────────────────────┤  │
                    │  │ Coding Arena Service <──> Isolated Execution     │  │
                    │  │                            Worker (Sandbox)      │  │
                    │  ├──────────────────────────────────────────────────┤  │
                    │  │ Unified AI Brain (Gemini / Fallback Engine)      │  │
                    │  └──────────────────────────┬───────────────────────┘  │
                    └─────────────────────────────┼──────────────────────────┘
                                                  ▼
                    ┌────────────────────────────────────────────────────────┐
                    │             PERSISTENCE & DATA STORAGE                 │
                    │  ┌──────────────────────┐    ┌──────────────────────┐  │
                    │  │ PostgreSQL Relational│    │ Local Storage/SQLite │  │
                    │  │ Database (Production)│    │ Test Isolation       │  │
                    │  └──────────────────────┘    └──────────────────────┘  │
                    └────────────────────────────────────────────────────────┘
```

## 2. Core Functional Modules (A through R)

1. **Module A: Unified AI Brain**
   - Abstraction interface for LLMs (`BaseAIProvider` with implementations for Gemini, Local Heuristic Engine, and Mock Provider for tests).
   - User context aggregation: dynamic student profile summary, strengths, skill gaps, learning speed, past errors.
   - Guardrails: prompt sanitization, output schema validation, token tracking, offline fallback.

2. **Module B: AI Career Copilot**
   - Adaptive career roadmap generator (Frontend/Backend/FullStack/Data/ML tracks).
   - Placement Readiness Index (0-100 score computed via weighted evaluation of Coding, Assessments, Resume, and Mock Interviews).
   - Dynamic weekly sprints with measurable milestones.

3. **Module C: Assessment Intelligence**
   - Time-bound testing engine with auto-save and interrupted session recovery.
   - Question randomization, negative marking mechanics, tag-based difficulty adaptation.
   - Comprehensive post-test analytics with topic-level diagnostic breakdown.

4. **Module D & E: Coding Arena & AI Code Review**
   - Multi-language code editor (Python, Java, C, C++).
   - Process-isolated execution worker with memory ceilings (128MB), timeout limits (3-5s), and zero network egress.
   - AI review pipeline for cyclomatic complexity, code smell detection, time/space optimality, and edge-case vulnerabilities.

5. **Module F: Interview Intelligence**
   - Voice/Text dual-mode AI interviewer with role-specific personas (Technical Lead, HR Partner, System Architect).
   - STAR methodology evaluation: Situation, Task, Action, Result scoring.
   - Detailed feedback report: tone, relevance, technical correctness, suggested response refinements.

6. **Module G & H: Smart Learning Hub & Spaced-Repetition Revision**
   - Concept breakdowns, interactive examples, practice problems mapped to topics.
   - SuperMemo SM-2 algorithm implementation for flashcards and weak-topic reinforcement.

7. **Module I: DSA Visualizer**
   - Interactive step-by-step state visualization for Graph algorithms (BFS, DFS, Dijkstra, Bellman-Ford, Kruskal, Prim, Topological Sort) and Dynamic Programming (0/1 Knapsack, LCS, LIS, Coin Change, Edit Distance).

8. **Module J & K: Resume & GitHub Intelligence**
   - ATS score analyzer, keyword gap scanner, section-by-section recommendation engine.
   - GitHub API analyzer calculating commit velocity, repository quality, code diversity, and README documentation depth.

9. **Module L & M: Job Intelligence & Placement Cell Dashboard**
   - Job opportunity aggregator and application tracker.
   - Institutional placement drive manager: batch-wise eligibility criteria, student roster filters, shortlisting, offer tracking, and PDF/CSV export.

10. **Module N: Admin Intelligence**
    - Platform overview: user management, question curation approval queue, system health metrics, audit logs, and security telemetry.

11. **Module O & P: Peer Learning & Notification System**
    - Discussion forums, peer coding rooms, and study groups.
    - Centralized in-app and email alert notification queue.

12. **Module Q & R: Security, Privacy & System Telemetry**
    - OWASP Top 10 mitigation: IDOR checks, bcrypt password hashing, strict JWT signature checks, input sanitization.
    - System health check endpoints (`/health/live`, `/health/ready`), structured logging, and automated backup hooks.

## 3. Technology Matrix & Version Standards

- **Node.js:** v24.x (LTS compatible)
- **Frontend Framework:** Next.js 14+ (App Router), React 18/19, Tailwind CSS v3/v4, Lucide Icons, Framer Motion
- **Python Backend:** Python 3.13+, FastAPI 0.115+, Pydantic v2, SQLAlchemy 2.0+, Uvicorn, Passlib (bcrypt), PyJWT
- **Database Engine:** PostgreSQL 15+ / SQLite3 (Harness test runtime)
- **Containerization:** Docker Compose v2+
