# NEXORA AI — PHASE 12 OBSERVABILITY & TELEMETRY ARCHITECTURE
## Privacy-Preserving Observability, Request Tracing & Operational Health

**Date:** 2026-11-26  
**Auditor:** Antigravity Systems Architect  
**Workspace:** `E:\NEXORA-AI-main\NEXORA-AI-main`  

---

## 1. Observability Architecture Overview

Phase 12 establishes a unified, privacy-preserving observability foundation for NEXORA AI:
1. **Context-Aware Structured JSON Logging:** Powered by Python's `logging` module and `JSONFormatter` in `backend/app/core/logging.py`, integrated with Python 3.13 `ContextVar` (`request_id_ctx`) for automated propagation across async task boundaries.
2. **End-to-End Request Correlation (`X-Request-ID`):** Automatically ingested from client requests or generated via UUIDv4, injected into response headers, and linked to server log records.
3. **In-Memory Operational Metrics Collector:** High-throughput `MetricsCollector` in `backend/app/core/telemetry.py` recording total requests, latency averages, HTTP status distribution, route counts, authentication failure rates, rate limit triggers, sync operations, and sandbox executions.
4. **Health Check Hierarchy:** Differentiated liveness (`/health/live`) and readiness (`/health/ready`) endpoints, featuring automated database ping probes without exposing internal credentials.

---

## 2. Privacy-Preserving Telemetry Rules

To ensure strict compliance with user data privacy standards:
- **Zero Secret Ingestion:** The metrics collector and structured logs strictly reject ingestion of:
  - User passwords or raw hashes
  - JWT access tokens or refresh tokens
  - API keys or biometric secrets
  - OTP values or password reset tokens
  - Student personal notes, resume text, or private discussion messages
- **Anonymized Aggregation:** Route distributions normalize parameters into path prefixes (e.g., `/api/v1/auth`, `/api/v1/sync`). No student UUIDs are used as metric keys.

---

## 3. Endpoints and Operational Interpretation

| Endpoint | Method | Scope / Output | Operational Meaning |
|---|---|---|---|
| `/health/live` | `GET` | `{"status": "ok", "app": "NEXORA AI"}` | Indicates the process is responsive and event loop is running. |
| `/health/ready` | `GET` | Health model containing `status`, `database`, `ai_engine`, `sandbox` | Executes live `SELECT 1` database query probe. Returns `"healthy"` if DB is responsive, `"degraded"` if disconnected. |
| `/metrics` | `GET` | Summary dictionary | Aggregated runtime metrics: `total_requests`, `average_latency_ms`, `status_distribution`, `auth_failures`, etc. |

---

## 4. Local Monitoring & Verification Instructions

Operators can query health and telemetry locally:
```bash
# 1. Probe application liveness
curl -s http://127.0.0.1:8000/health/live

# 2. Probe application readiness and DB connectivity
curl -s http://127.0.0.1:8000/health/ready

# 3. View operational metrics
curl -s http://127.0.0.1:8000/metrics
```
