# Phase 15B: Staging Architecture Design

## 1. Architectural Topology
The NEXORA AI staging environment is designed as a fully isolated, multi-tier system mirroring production while preventing data leakage or accidental connection to external production services:

```
+-------------------------------------------------------------------------+
|                       NEXORA AI STAGING TOPOLOGY                        |
+-------------------------------------------------------------------------+
|                                                                         |
|  [ Mobile Client: Expo 52 ]      [ Frontend: Next.js 14 App Router ]    |
|   - Staging API Routing           - Dedicated Staging Port (3001)       |
|   - Local SQLite SM-2 Queue       - Strict CORS Binding                 |
|            |                                    |                       |
|            +-----------------+------------------+                       |
|                              |                                          |
|                              v                                          |
|                 [ Backend: FastAPI Staging ]                            |
|                  - Dedicated Staging Port (8001)                        |
|                  - Argon2id Password Hashing                            |
|                  - JWT RBAC & Telemetry                                 |
|                  - Fail-Closed Sandbox Supervisor                       |
|                              |                                          |
|            +-----------------+------------------+                       |
|            |                                    |                       |
|            v                                    v                       |
|  [ PostgreSQL 17 Staging ]            [ Coding Arena Sandbox ]          |
|   - DB: nexora_staging                 - Mode: container_isolated       |
|   - Dedicated Staging Role             - Fail-Closed if Daemon Offline  |
|                                                                         |
+-------------------------------------------------------------------------+
```

## 2. Staging Isolation Controls
- **Dedicated Network Ports:** Backend runs on port `8001` (avoiding standard `8000`), Frontend on port `3001` (avoiding `3000`).
- **Database Segregation:** Staging operates against `nexora_staging` / isolated staging SQLite instances; `nexora_dev.db` is strictly locked and untouched.
- **Fail-Closed Sandbox:** When container runtime is absent, Coding Arena rejects untrusted execution with HTTP 200 payload `EXECUTION_BLOCKED_SECURITY_POLICY`.
- **Telemetry & Logging:** Staging metrics and request IDs are correlated with `X-Request-ID` and logged to dedicated staging streams.
