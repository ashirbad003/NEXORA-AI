# NEXORA AI — PHASE 5 REMAINING RISKS & MITIGATION MATRIX
**Product:** NEXORA AI  
**Tagline:** Intelligence That Moves You Forward.  
**Phase:** 5 (Coding Arena & Isolated Sandbox Worker)  
**Date:** November 20, 2026  
**Auditor:** Principal DevSecOps & Security Architect  

---

## 1. Executive Summary

This document enumerates the technical, architectural, operational, and security risks identified during the Phase 5 implementation and testing cycle, along with active mitigations and recommended operational runbooks.

---

## 2. Risk Matrix

| Risk ID | Category | Description | Severity | Likelihood | Mitigation Status | Operational Recommendation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RSK-501** | Security / Infra | Docker Daemon Availability on Windows Host | High | Medium | **Mitigated (Fail-Closed)** | Sandbox fails closed with `EXECUTION_BLOCKED_SECURITY_POLICY` when Docker daemon pipe is unreachable. Untrusted code is never run on host. Production deployment should run on a Linux host with a dedicated Docker daemon or rootless container runtime (`podman` / `containerd`). |
| **RSK-502** | Security / Sandbox | Container Escape or Kernel Exploits | Critical | Low | **Mitigated** | Multi-layer containment: `--cap-drop ALL`, `--security-opt no-new-privileges`, read-only rootfs (`--read-only`), non-root UID 1000, `--network none`, strict CPU (0.5 cores) and RAM (128MB) limits. |
| **RSK-503** | Performance | Cold Start Latency for Compiler Toolchains | Medium | High | **Planned** | Compiling C/C++ or bootstrapping JVM inside on-demand disposable containers introduces 400ms–1200ms latency. In production, maintain a warm worker pool of pre-pulled containers or a lightweight gRPC worker daemon. |
| **RSK-504** | Security / Data | Hidden Test Case Exfiltration | High | Low | **Mitigated** | Frontend APIs strictly filter `is_sample=False` test cases. Evaluations execute server-side; test case outputs are never reflected back unless configured as a sample. |
| **RSK-505** | Availability | Denial of Service via Submission Flooding | Medium | Medium | **Partially Mitigated** | Current endpoint enforces token-based authentication and database transactional records. Rate limiting middleware (e.g. 5 submissions/min per user via Redis token bucket) should be deployed before public traffic. |
| **RSK-506** | Data Integrity | Concurrent Submission Streak Race Conditions | Low | Low | **Mitigated** | Streak calculations use atomic transactional updates with date delta calculations inside `backend/app/services/coding_service.py`. |

---

## 3. Operational Requirements for Live Execution

To enable active code evaluation in local development or production:
1. Ensure the Docker daemon is running:
   ```bash
   docker info
   ```
2. Pre-pull the official minimal sandbox runner images:
   ```bash
   docker pull python:3.11-alpine
   docker pull gcc:latest
   docker pull openjdk:17-alpine
   ```
3. Set the environment variable in `backend/.env`:
   ```env
   SANDBOX_MODE="container_isolated"
   ```
4. If running in an unisolated environment (e.g., bare Windows without Docker), keep:
   ```env
   SANDBOX_MODE="disabled"
   ```
   The platform will gracefully inform the user of the security restriction without crashing or risking system integrity.
