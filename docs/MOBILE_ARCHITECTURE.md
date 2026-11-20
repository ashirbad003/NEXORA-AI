# NEXORA AI - Android Mobile Architecture & Integration Strategy

**Framework:** React Native with Expo (Managed Workflow)  
**Target Platform:** Android (API Level 26+)  
**Target Bundle:** APK / AAB (`ai.nexora.app`)  

---

## 1. Architectural Alignment with Unified Backend

The Android mobile application is not a detached product; it is a synchronized native client to the NEXORA AI REST API:

```
[ Android Client (React Native / Expo) ]
                │
                ▼
  [ Secure Token Vault (Expo SecureStore) ]
  - AES-encrypted storage of Access and Refresh tokens
                │
                ▼
  [ Unified REST API (FastAPI Backend) ]
  - Identical endpoints used by Next.js Web App
  - Shared authentication state, student profiles, and test attempts
```

---

## 2. Core Mobile Capabilities (Module-by-Module)

1. **Shared Authentication & Biometric Unlock:**
   - Unified login/signup with backend JWT authentication.
   - Biometric fingerprint/face unlock using device secure enclave.
2. **AI Career Copilot in Your Pocket:**
   - Instant mobile access to daily sprint checklists, milestone progress, and career roadmaps.
3. **Smart Revision & Flashcards On-the-Go:**
   - Touch-optimized card flip gestures with SuperMemo SM-2 algorithm.
   - Offline flashcard cache allowing revision on transit without internet.
4. **Push Notifications (FCM / Expo Push):**
   - Scheduled reminders for daily streaks, assessment deadlines, and campus placement drive announcements.

---

## 3. Build & Deployment Structure

- **Development:** Expo Go client on physical Android device or Android Virtual Device (AVD).
- **Release Compilation:** Standalone Android APK generation via `eas build -p android --profile preview` or local gradle release runner.
- **Limitation Note:** Mobile compilation and APK testing require complete React Native dependencies to be installed in Phase 11. In Phase 1, the foundational package manifests, Expo configuration, and architecture plans are anchored.
