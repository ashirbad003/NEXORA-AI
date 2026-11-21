# NEXORA AI — PHASE 8 DEPENDENCY ANALYSIS
## Upstream Integrations & Prerequisites

**Workspace:** `E:\NEXORA_AI`  
**Phase:** 8 (Resume, GitHub & Job Intelligence)  
**Status:** **VERIFIED**

---

## 1. Upstream Dependencies
- **Authentication & User Profile (`FEAT-311`, `StudentProfile`):** Supplies student skills, projects, and career preferences for resume builders and job match calculations.
- **Unified AI Brain (Phase 6):** Powers ATS scoring, JD gap analysis, action verb enhancers, and cold email generators via `ai_engine.providers.factory`.
- **Public & Free GitHub API:** Fetches public user repository metadata, languages, commit activity, and README content without requiring commercial paid services.
- **Database Architecture:** Forward Alembic migration to house resume versions, job postings, student job applications, and GitHub cache models.
