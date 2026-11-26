# NEXORA AI — PHASE 11C IMPLEMENTATION BLUEPRINT
## Mobile Student Dashboard, Flashcard Revision Hub, Offline SM-2 & Mistake Notebook

**Project:** NEXORA AI  
**Subphase:** 11C  
**Author:** Antigravity AI  
**Scope:** Mobile UI, Offline Queue, Spaced Repetition Engine, and Mistake Notebook  

---

## 1. Executive Overview & Scope
Phase 11C delivers the core student learning and revision interface on mobile:
1. **Student Dashboard:** Real-time summary of student career readiness score, decks overview, cards due count, review streak, daily activity stats, and quick learning actions.
2. **Touch-Optimized Flashcard Hub:** Deck selection, interactive flip card review with front prompt/code snippet and back answer/explanation, SM-2 rating buttons (0 to 5), session progress bar, and session completion celebration.
3. **Canonical SM-2 Engine Integration:** Local provisional SM-2 calculations matching `backend/app/services/sm2_service.py` exactly (`EF'`, `repetition`, `interval_days`, `stability`), server-authoritative submission with server state version tracking (`base_state_version`).
4. **Offline Revision Queue:** Persistent local queue for reviews performed without network connectivity, preventing data loss, avoiding duplicates via UUID idempotency keys, and batch-flushing via `POST /api/v1/sync/push` or `/api/v1/revision/reviews/submit` upon reconnection.
5. **Mistake Notebook:** Listing student mistakes categorized by source (coding, assessment, manual), viewing question context and error messages, and marking items resolved.
6. **Accessible Navigation:** Bottom tab or segment navigation seamlessly switching between Dashboard, Flashcard Decks, Mistake Notebook, and Profile.

---

## 2. Component & Directory Architecture
```
mobile/src/
├── api/
│   ├── revision.ts           # Revision decks, cards, due cards, stats, mistake notebook endpoints
│   ├── sync.ts               # Sync push and pull operations
│   └── revisionTypes.ts      # Deck, Card, Mistake, Review, and Sync request/response types
├── services/
│   ├── offlineQueue.ts       # SecureStore-backed offline review action queue
│   └── localSm2.ts           # Local provisional SM-2 calculator matching backend canonical rules
├── components/
│   ├── revision/
│   │   ├── FlipCard.tsx      # Smooth flip card component with animated front/back reveal
│   │   ├── RatingBar.tsx     # 0-5 SM-2 grade buttons (Blackout, Hard, Pass, Good, Easy)
│   │   ├── DeckCard.tsx      # Deck item card with category, tags, and due count badge
│   │   └── StreakBadge.tsx   # Cyber Lime streak counter badge
│   └── mistakes/
│       └── MistakeItem.tsx   # Mistake notebook row with status pill and resolve toggle
├── screens/
│   ├── DashboardScreen.tsx   # Main student dashboard with readiness, stats, and shortcuts
│   ├── DecksScreen.tsx       # Flashcard deck catalog and due card summary
│   ├── ReviewSessionScreen.tsx # Interactive touch revision session with flip card & SM-2
│   └── MistakeNotebookScreen.tsx # Mistake notebook directory with filter and resolve actions
└── tests/
    ├── localSm2.test.ts      # Unit tests for canonical SM-2 calculation equivalence
    ├── offlineQueue.test.ts  # Unit tests for offline queue enqueue, persistence, and deduplication
    └── revisionApi.test.ts   # Contract tests for revision and mistake endpoints
```

---

## 3. Detailed Acceptance Criteria
- [x] **AC-11C-01 (Dashboard):** Displays readiness score, cards due, streak days, total decks, and navigation shortcuts with pull-to-refresh.
- [x] **AC-11C-02 (Flashcard Revision):** Decks load from `/revision/decks`; review session fetches `/revision/cards/due`; cards flip cleanly with revealed answers.
- [x] **AC-11C-03 (SM-2 Precision):** Rating input 0..5 generates deterministic interval and ease factor matching the backend SM-2 algorithm.
- [x] **AC-11C-04 (Offline Queue):** If network is offline, review operations are enqueued locally with unique idempotency keys, persisted safely, and auto-flushed when online.
- [x] **AC-11C-05 (Mistake Notebook):** Displays mistakes from `/revision/mistakes`, renders context/error, and allows resolving mistakes via `/revision/mistakes/{id}/resolve`.
- [x] **AC-11C-06 (Strict Quality & Safety):** Zero TypeScript errors, 100% tests passing, zero hardcoded credentials, zero unpushed Git claims.
