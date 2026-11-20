# NEXORA AI - Intelligent Career, Learning & Placement Ecosystem

> **Tagline:** Intelligence That Moves You Forward.  
> **Mission:** Deliver a unified, enterprise-grade AI-powered career development, skill evaluation, interview preparation, and placement ecosystem for students, administrators, and placement cells.

---

## 1. System Overview & Architecture

NEXORA AI is organized as a multi-tier, modular platform comprising:
- **Frontend Web Application:** Next.js (App Router), TypeScript, Tailwind CSS, Cybernetic Obsidian design system (`#060913`, `#a3e635`, `#8b5cf6`), responsive PWA.
- **Backend API Engine:** Python FastAPI, Pydantic v2, SQLAlchemy 2.0 (asyncio-ready), JWT authentication with secure refresh tokens, Role-Based Access Control (`STUDENT`, `ADMIN`, `PLACEMENT_CELL`).
- **Database Architecture:** PostgreSQL (production target via Docker/Cloud) with SQLite fallback for local test harness; strict relational integrity, indexed foreign keys, automated schema migrations.
- **Unified AI Brain (Module A):** Provider-agnostic AI orchestration (supporting Gemini, Ollama, HuggingFace, OpenAI compatible endpoints, and deterministic local algorithmic fallbacks for offline stability).
- **Secure Code Execution Worker (Module D/Sandbox):** Process-isolated, resource-constrained, non-host execution worker with timeout guards, memory limits, and sanitized I/O.
- **Mobile Client:** Dedicated cross-platform application (React Native / Expo) bound to the unified REST API with offline cache and sync capabilities.
- **Institutional & Admin Portals:** Complete placement drive recruitment workflows, batch eligibility filters, performance analytics, question bank curation, and real-time audit telemetry.

---

## 2. Directory Layout & Repository Standard

```
E:\NEXORA_AI/
├── backend/                  # FastAPI Application Core
│   ├── app/
│   │   ├── api/              # v1 API routers (auth, student, coding, assessment, ai, etc.)
│   │   ├── core/             # Configuration, security, JWT, rate limiting
│   │   ├── db/               # Session management, migrations, base models
│   │   ├── models/           # SQLAlchemy entity models
│   │   ├── schemas/          # Pydantic validation models
│   │   ├── services/         # Business logic & AI orchestration
│   │   └── utils/            # Helper utilities, logger, sanitizers
│   ├── alembic/              # Database migration scripts
│   ├── requirements.txt      # Python dependencies
│   └── tests/                # Unit, integration, security tests
├── frontend/                 # Next.js App Router Web Platform
│   ├── src/
│   │   ├── app/              # Routes & layouts (landing, student, admin, placement, etc.)
│   │   ├── components/       # Reusable atomic UI system & widgets
│   │   ├── hooks/            # Custom client hooks
│   │   ├── lib/              # API clients, auth helpers, utility functions
│   │   └── styles/           # Tailwind CSS design tokens & animations
│   ├── public/               # Static assets & brand media
│   └── package.json          # Frontend dependencies
├── mobile/                   # Android / React Native / Expo Application
│   ├── app/                  # Screens & navigation
│   ├── components/           # Mobile design system components
│   └── package.json          # Mobile dependencies
├── sandbox/                  # Isolated code execution worker
│   ├── executor.py           # Process isolation runner & resource limits
│   └── tests/                # Sandbox security tests
├── infrastructure/           # Docker Compose, Nginx reverse proxy, configs
│   ├── docker-compose.yml
│   └── nginx/
├── docs/                     # Full engineering documentation & registries
│   ├── MASTER_FEATURE_REGISTRY.md
│   ├── FEATURE_TRACEABILITY_MATRIX.md
│   ├── FEATURE_IMPLEMENTATION_STATUS.md
│   ├── FEATURE_DEPENDENCY_MAP.md
│   ├── DATABASE_SCHEMA.md
│   └── PROJECT_ARCHITECTURE.md
├── scripts/                  # Automation, seeding, and verification scripts
└── README.md
```

---

## 3. Core Design Tokens & Visual Identity

- **Obsidian Dark (Base Background):** `#060913`
- **Surface Elevation (Cards/Panels):** `#0c1222`, `#131b31`
- **Cyber Lime (Primary Action & Accent):** `#a3e635`
- **Tech Violet (Intelligence & Secondary Accent):** `#8b5cf6`
- **Border Gradients:** Cyber Lime to Tech Violet subtle glow (`rgba(163, 230, 53, 0.2)` to `rgba(139, 92, 246, 0.2)`)
- **Typography:** Inter, JetBrains Mono (for coding arena & terminal views).

---

## 4. Phase-by-Phase Roadmap

- **Phase 0:** Requirements, Architecture, Master Feature Catalog (300+ items), Discovery.
- **Phase 1:** Core Repository, Shared Config, Design System Foundations.
- **Phase 2:** Database Architecture, Models, Centralized Authentication & RBAC.
- **Phase 3:** Core REST API endpoints and Web Frontend shell integration.
- **Phase 4:** Student Dashboard, Learning Hub & Concept Exploration.
- **Phase 5:** Coding Arena, Multi-Language Runner & Sandboxed Execution.
- **Phase 6:** Unified AI Brain & AI Career Copilot.
- **Phase 7:** Assessment Intelligence & AI Mock Interview Studio.
- **Phase 8:** Resume Parser & Builder, GitHub Analyzer, Job Opportunity Discovery.
- **Phase 9:** Placement Cell Portal & Enterprise Admin Intelligence.
- **Phase 10:** Smart Spaced-Repetition Revision (SM-2), Peer Discussions, Notification Hub.
- **Phase 11:** Android Mobile Application & Synchronized Cross-Device State.
- **Phase 12:** System Telemetry, Health Diagnostics & Security Hardening.
- **Phase 13:** Regression Testing, Verification & Recovery Drills.
- **Phase 14:** Final Comprehensive Audit and Release Verification.
