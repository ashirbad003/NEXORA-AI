# Phase 15D: PostgreSQL Staging Report

## 1. Executive Summary
This report documents the staging database provisioning strategy, Alembic migration verification, and schema consistency for the PostgreSQL 17 staging target.

## 2. Alembic Migration History & Lineage
The migration history was audited and verified linear without branching or divergence:
1. `<base> -> 831b7c542bb8`: `initial_core_auth_and_rbac_tables`
2. `831b7c542bb8 -> 639a0bda8ebc`: `phase_4_learning_and_progress_tables`
3. `639a0bda8ebc -> 74a123b456cd`: `phase_4_topic_feedback_table`
4. `74a123b456cd -> 92c890123def`: `phase_5_coding_arena_tables`
5. `92c890123def -> a3ebe19fb261`: `phase_6_copilot_tables`
6. `a3ebe19fb261 -> b7fcde829101`: `phase_7_assessment_and_interview_tables`
7. `b7fcde829101 -> c8a1fe910202`: `phase_8_resume_github_job_tables`
8. `c8a1fe910202 -> d9b2ef020303`: `phase_9_placement_and_admin_portal_tables`
9. `d9b2ef020303 -> e1f2a3b4c5d6`: `phase_10_master_tables`
10. `e1f2a3b4c5d6 -> f2a3b4c5d6e7 (head)`: `phase_11_mobile_sync`

## 3. Provisioning Script & Security Controls
- **DDL Provisioning:** Script `scripts/postgres/provision_nexora_db.sql` enforces `ON_ERROR_STOP on`, verifies `NOINHERIT`, checks for unexpected role memberships, and enforces least-privilege role boundaries (`NOCREATEDB NOCREATEROLE NOBYPASSRLS`).
- **Isolation Invariant:** Routine migrations and live staging tests are strictly prohibited from touching `nexora_dev` or development databases.
- **Runtime Environment:** Service `postgresql-x64-17` is confirmed running on port 5432. Staging credentials connect to dedicated staging catalogs (`nexora_staging`).
