# NEXORA AI: Password Security Review & Argon2id Architecture Decision

**Auditor:** Independent Security & Cryptographic Review Lead  
**Audit Target:** `backend/app/core/security.py`, `backend/app/core/config.py`  
**Status:** **REMEDIATED & VERIFIED (Argon2id Memory-Hard Profile)**  
**Date:** November 19, 2026  

---

## 1. Vulnerability Assessment: SHA-256 for Password Storage

### Initial Implementation Finding:
In Phase 1, password hashing was initially implemented using salted SHA-256 (`hashlib.sha256((salt + password).encode())`).

### Cryptographic Security Risk:
1. **ASIC & GPU Parallel Computation:** SHA-256 is designed for fast digest computation in message integrity checks. Modern high-end GPUs (e.g. RTX 4090) can calculate over **10 billion SHA-256 hashes per second**. A salted single-round SHA-256 hash provides virtually zero defense against offline dictionary or brute-force attacks if a database dump is leaked.
2. **Zero Memory Hardness:** Fast digest algorithms consume negligible RAM during execution. Attackers can instantiate millions of parallel hashing cores on custom FPGA/ASIC hardware.
3. **OWASP & NIST Password Storage Standards:** OWASP and NIST SP 800-63B explicitly mandate memory-hard password derivation functions: **Argon2id (Winner of the Password Hashing Competition)**, scrypt, or bcrypt (cost factor >= 12). SHA-256 alone is explicitly prohibited for credential storage.

---

## 2. Remediation Strategy & Implementation

We have eradicated the preliminary SHA-256 implementation and replaced it with **Argon2id via `argon2-cffi`**.

### Configured Argon2id Cryptographic Parameters:
```python
# RFC 9106 Recommended Standard Profile
time_cost = 2       # 2 iterations
memory_cost = 65536 # 64 MB of RAM per hash
parallelism = 4     # 4 parallel threads
hash_len = 32       # 32 bytes output digest
salt_len = 16       # 16 bytes cryptographically secure random salt
```

### Security Properties Achieved:
1. **Memory-Hard Defense:** By requiring 64 MB of RAM per password evaluation, large-scale parallel GPU/ASIC attacks are rendered economically and hardware-wise infeasible.
2. **Argon2id Hybrid Resistance:** Argon2id combines Argon2d (data-dependent indexing for GPU resistance) and Argon2i (data-independent indexing for side-channel timing attack resistance).
3. **Constant-Time Verification:** Handled natively by the audited CFFI binding (`_password_hasher.verify()`).
4. **Safe Error Trapping:** Mismatches and malformed inputs raise typed exceptions (`VerifyMismatchError`, `InvalidHashError`) trapped safely to return `False` without leaking stack traces or crashing the event loop.

---

## 3. Automated Verification Evidence

Executed in [tests/unit/test_password_security.py](file:///e:/NEXORA_AI/tests/unit/test_password_security.py):
- `test_argon2id_hashing_and_verification`: PASS (Hash starts with `$argon2id$v=19$m=65536,t=2,p=4$`)
- `test_empty_password_rejection`: PASS (Raises `ValueError`)
- `test_malformed_hash_handling`: PASS (Returns `False` cleanly)
- `test_constant_time_different_length_inputs`: PASS (Evaluated safely)
- `test_salt_uniqueness`: PASS (Two hashes of same password yield distinct salts)
- `test_rehash_check`: PASS (Validates parameters)
