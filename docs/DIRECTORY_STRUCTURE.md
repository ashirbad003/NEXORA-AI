# NEXORA AI - Repository Directory Structure & Module Responsibilities

This document defines the architectural organization of the NEXORA AI monorepo. Every directory has a strictly defined domain responsibility.

---

```
E:\NEXORA_AI/
├── ai-engine/                  # Unified AI Brain Core (Provider-agnostic interface)
│   ├── providers/              # Gemini, Local Deterministic Fallback, Mock implementations
│   ├── prompts/                # Version-controlled prompt templates & personas
│   ├── guardrails/             # Input sanitization, safety filters, output schema validators
│   └── telemetry/              # Token accounting, latency monitors, cost telemetry
│
├── backend/                    # Core REST API Platform (FastAPI)
│   ├── app/
│   │   ├── api/                # v1 Route controllers (auth, student, coding, assessment, etc.)
│   │   ├── core/               # Pydantic BaseSettings, JWT security, CORS, rate limiting
│   │   ├── db/                 # Database session factory, base model, migration hooks
│   │   ├── models/             # SQLAlchemy 2.0 ORM domain entities
│   │   ├── schemas/            # Pydantic v2 validation schemas
│   │   ├── services/           # Business domain logic layers
│   │   └── utils/              # Structured JSON logging, password hashing, IDOR helpers
│   ├── alembic/                # Database migration environment
│   ├── requirements.txt        # Python backend dependencies
│   └── main.py                 # FastAPI application factory entry point
│
├── frontend/                   # Web Platform (Next.js App Router & Tailwind CSS)
│   ├── src/
│   │   ├── app/                # App Router pages and layouts
│   │   ├── components/         # Reusable atomic UI system (Button, Card, Badge, Modal, etc.)
│   │   ├── hooks/              # Custom React hooks (auth, query, theme)
│   │   ├── lib/                # API client, token storage, utilities
│   │   └── styles/             # Tailwind theme extensions & CSS variables
│   ├── public/                 # Static assets, branding, and manifest
│   ├── package.json            # Node.js frontend dependencies
│   ├── tsconfig.json           # TypeScript configuration
│   └── tailwind.config.js      # Tailwind CSS configuration with Cyber Obsidian tokens
│
├── mobile/                     # Android / Cross-Platform Application (React Native / Expo)
│   ├── app/                    # Mobile screens & navigation tabs
│   ├── components/             # Mobile-optimized UI components
│   ├── services/               # Shared mobile API client & secure storage
│   ├── package.json            # Mobile dependencies
│   └── app.json                # Expo application manifest & Android build config
│
├── database/                   # Database Architecture & Management
│   ├── schema/                 # Relational schema DDL definitions
│   ├── seeds/                  # Seed datasets (100+ companies, curated problems)
│   ├── migrations/             # Migration change scripts
│   └── backups/                # Backup scripts and recovery validation tools
│
├── sandbox/                    # Process-Isolated Coding Execution Platform
│   ├── worker.py               # Process isolation runner with timeouts and resource caps
│   ├── jail.py                 # Filesystem and process permission boundary
│   └── tests/                  # Security tests against malicious code execution
│
├── infrastructure/             # Containerization & Deployment
│   ├── docker-compose.yml      # Orchestrated services (API, DB, Sandbox, Nginx)
│   ├── nginx/                  # Reverse proxy, SSL, and rate-limiting configuration
│   └── env/                    # Environment variable templates for deployment stages
│
├── tests/                      # Automated Verification & Test Suites
│   ├── unit/                   # Backend & frontend unit tests
│   ├── integration/            # API endpoint integration tests
│   ├── security/               # IDOR, auth, and sandbox security tests
│   └── e2e/                    # End-to-end user workflow verification
│
├── scripts/                    # Operational automation & validation utilities
├── docs/                       # Complete engineering documentation & registries
├── README.md                   # Project overview & roadmap
├── PROJECT_STATUS.md           # Live progress tracker
├── .env.example                # Environment variable configuration template
└── .gitignore                  # Git repository exclusion rules
```
