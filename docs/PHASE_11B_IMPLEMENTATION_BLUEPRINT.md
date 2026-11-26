# NEXORA AI — PHASE 11B ARCHITECTURE & IMPLEMENTATION BLUEPRINT
## Mobile Scaffolding, Secure Vault, Authentication & Biometrics

**Project:** NEXORA AI  
**Subphase:** 11B  
**Author:** Antigravity AI  
**Scope:** Client-side React Native / Expo Architecture for `mobile/`  

---

## 1. Objectives & Scope
Phase 11B establishes the foundational mobile application architecture for NEXORA AI, implementing:
1. Strict modular Expo/React Native scaffolding (`mobile/src/`).
2. Centralized Axios HTTP client with mutex-controlled automatic 401 token refresh queue.
3. Secure credential lifecycle with `expo-secure-store` protecting JWT access and refresh tokens.
4. Biometric authentication using `expo-local-authentication` (fingerprint/face recognition) protecting local app unlock with secure fallback to password.
5. React Context based Auth Provider managing session state (`isAuthenticated`, `isBiometricEnrolled`, `isLocked`, `user`).
6. Polished Cybernetic Obsidian styled screens:
   - Login Screen (`/login`)
   - Registration Screen (`/register`)
   - Biometric Lock/Unlock Screen (`/unlock`)
   - Main Student Shell (`/home` / Student Overview) with logout and biometric toggle.
7. Unit and integration tests for auth client, secure vault, and biometric service.

---

## 2. Directory Structure Specification (`mobile/`)
```
mobile/
├── app.json
├── package.json
├── tsconfig.json
├── App.tsx
├── src/
│   ├── api/
│   │   ├── client.ts             # Axios instance, interceptors, 401 mutex refresh queue
│   │   ├── auth.ts               # Login, register, refresh, logout, getMe API calls
│   │   └── types.ts              # Request/response interfaces aligned with backend
│   ├── services/
│   │   ├── secureStore.ts        # Expo SecureStore token vault wrapper
│   │   └── biometrics.ts         # Expo LocalAuthentication helper & enrollment check
│   ├── context/
│   │   └── AuthContext.tsx       # AuthProvider, state machine, lifecycle hooks
│   ├── screens/
│   │   ├── LoginScreen.tsx       # Obsidian dark login screen
│   │   ├── RegisterScreen.tsx    # Student registration screen
│   │   ├── BiometricLockScreen.tsx # Biometric unlock overlay
│   │   └── HomeScreen.tsx        # Authenticated student landing & session status
│   ├── components/
│   │   ├── common/
│   │   │   ├── Button.tsx        # Cyber Lime / Tech Violet animated button
│   │   │   ├── Input.tsx         # Accessible obsidian form input
│   │   │   └── Card.tsx          # Elevated obsidian card surface
│   ├── navigation/
│   │   └── RootNavigator.tsx     # State-driven routing (Auth vs App vs Locked)
│   ├── theme/
│   │   └── colors.ts             # NEXORA design tokens (#060913, #a3e635, #8b5cf6)
│   └── tests/
│       ├── secureStore.test.ts
│       ├── authClient.test.ts
│       └── biometrics.test.ts
```

---

## 3. Detailed Acceptance Criteria
- [x] **AC-11B-01 (Strict Scaffolding):** Clean Expo SDK 52 setup with TypeScript `strict: true`, zero build errors.
- [x] **AC-11B-02 (Secure Storage):** Tokens stored exclusively via `expo-secure-store` (never AsyncStorage, localStorage, or plaintext).
- [x] **AC-11B-03 (API Client & 401 Mutex):** Axios client transparently refreshes expired access tokens without triggering redundant concurrent `/auth/refresh` calls.
- [x] **AC-11B-04 (Biometric Security):** Local unlock guarded by `expo-local-authentication`. Biometrics gates local entry, while server sessions remain validated by JWT.
- [x] **AC-11B-05 (Screen Design & UX):** Responsive, dark-themed UI adhering to NEXORA Cyber Obsidian design tokens with field validation, loading indicators, and explicit error states.
- [x] **AC-11B-06 (Logout Hygiene):** Calling logout revokes the refresh token on the backend, wipes local secure store, resets biometric lock state, and routes to Login.
