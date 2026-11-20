# NEXORA AI — Authentication & Token Lifecycle Design
## Argon2id, JWT Architecture, Refresh Rotation & Revocation

**Date:** 2026-11-19  
**Specification Version:** 1.0  
**Security Level:** Enterprise Grade / Zero Trust Foundation  

---

## 1. Authentication Architecture Overview

NEXORA AI utilizes a dual-token stateless access / stateful refresh authentication mechanism backed by Argon2id password hashing:

```
[ Client ] -- 1. POST /auth/login (email, password) --> [ FastAPI Auth Service ]
                                                               |
                                              Verify Argon2id Hash in DB
                                                               |
[ Client ] <-- 2. Returns Access Token (15m) + Refresh Token (7d) --+
    |                                                          |
    |                                            Stores SHA-256(RefreshToken)
    |                                            in DB (`refresh_tokens`)
    |
    +-- 3. GET /api/v1/students/profile (Bearer Access Token) --> [ API Endpoint ]
    |                                                                   |
    |                                                      Stateless JWT Verification
    |                                                      (Signature + Exp + Roles)
    |
    +-- 4. POST /auth/refresh (RefreshToken) -------------> [ Auth Service ]
                                                                   |
                                                      1. Find Token by Hash in DB
                                                      2. Check Expiration & Revocation
                                                      3. Invalidate Old Token
                                                      4. Issue New Token Pair
[ Client ] <-- 5. Returns New Access + Refresh Token ----------+
```

---

## 2. Password Hashing Specification (Argon2id)

To defend against GPU and specialized ASIC brute-force attacks while mitigating side-channel timing analysis, NEXORA AI exclusively uses **Argon2id** (RFC 9106) via the `argon2-cffi` library.

### Configuration Parameters:
- **Variant:** Argon2id (hybrid data-dependent and data-independent memory access)
- **Time Cost (`t`):** `2` iterations
- **Memory Cost (`m`):** `65,536 KiB` (64 MB)
- **Parallelism (`p`):** `4` threads
- **Hash Length:** `32` bytes
- **Salt Length:** `16` bytes (cryptographically generated per password via `os.urandom`)

### Security Invariants:
1. Passwords are never logged, echoed, or stored in plaintext.
2. Verification executes in constant time via the native Argon2 C-binding.
3. Empty passwords or corrupt hashes raise explicit structured exceptions handled upstream.

---

## 3. JWT Token Claims & Verification

### 3.1 Access Token Structure
- **Algorithm:** `HS256` (Configurable to `RS256` / `Ed25519` for federated environments)
- **Time to Live (TTL):** `15 minutes` (`ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Claims Payload:**
  - `sub`: User UUID string
  - `email`: User email string
  - `role`: Primary role identifier (`student`, `admin`, etc.)
  - `type`: `"access"`
  - `jti`: Unique UUIDv4 token identifier (prevents identical token hashes)
  - `exp`: Expiration UNIX timestamp
  - `iat`: Issued-at UNIX timestamp

### 3.2 Refresh Token Structure
- **Algorithm:** `HS256`
- **Time to Live (TTL):** `7 days` (`REFRESH_TOKEN_EXPIRE_DAYS`)
- **Claims Payload:**
  - `sub`: User UUID string
  - `type`: `"refresh"`
  - `jti`: Unique UUIDv4 token identifier
  - `exp`: Expiration UNIX timestamp
  - `iat`: Issued-at UNIX timestamp

---

## 4. Refresh Token Rotation & Theft Detection

To guarantee that compromised refresh tokens cannot be indefinitely abused:
1. **One-Time Use (Rotation):** Every successful invocation of `/api/v1/auth/refresh` rotates the token:
   - The presented token's hash is queried in `refresh_tokens`.
   - The token record is marked `is_revoked = True` and `revoked_at = utc_now()`.
   - A fresh refresh token is minted, hashed, and stored in the database.
   - A fresh access token is minted and returned alongside the new refresh token.
2. **Replay / Reuse Detection:** If an incoming request presents an expired or already-revoked refresh token:
   - The authentication service logs an immediate high-severity security alert (`auth.token_reuse_detected`).
   - The transaction fails with `HTTP 401 Unauthorized`.
   - The system can optionally revoke all active refresh tokens for that user ID, enforcing a complete re-authentication.

---

## 5. Logout & Session Termination

Invoking `POST /api/v1/auth/logout`:
1. Requires a valid access token in the `Authorization: Bearer <token>` header.
2. Looks up all active non-revoked refresh tokens associated with `current_user.id` or the specific session.
3. Sets `is_revoked = True` on the tokens.
4. Records an audit event `auth.logout.success`.
