# NEXORA AI — PHASE 10 RISK & ROLLBACK PLAN

**Workspace:** `E:\NEXORA_AI`  
**Phase:** 10 (Smart Revision, Peer Learning & Notifications)  

---

## 1. Threat & Risk Assessment

| Risk Vector | Likelihood | Impact | Severity | Mitigation Strategy |
| :--- | :---: | :---: | :---: | :--- |
| **Notification Spam & Denial of Service** | Medium | Medium | Medium | Implement user-level rate limiting on notification creation (max 20 per minute) and deduplication hashes for identical alert payloads. |
| **Toxic / Inappropriate Forum Content** | High | High | High | Auto-moderation heuristic interceptor in `PeerService` that quarantines flagged content before rendering; one-click student reporting workflow (`FEAT-292`). |
| **IDOR & Unauthorized Card Deck Access** | Medium | High | High | Strict ownership enforcement: `deck.user_id == current_user.id or deck.is_public == True`; study circle decks verify circle membership. |
| **WebSocket Connection Saturation** | Low | Medium | Medium | Connection heartbeat (30s ping/pong), max 3 concurrent active WebSocket sessions per user ID, graceful disconnect on idle. |
| **Mistake Notebook Memory/Storage Bloat** | Medium | Low | Low | Enforce max 500 error entries per student with auto-cleanup of resolved errors. |
| **Email SMTP Credential Exposure / Failures** | Low | High | Medium | Store SMTP configuration strictly via environment variables; fail closed to mock console logger if SMTP host is unreachable; zero crash propagation. |

---

## 2. Reversible Database Migration & Rollback Strategy

1. **Forward-Only, Non-Destructive Migration:**
   - The Phase 10 migration will only issue `CREATE TABLE` and `CREATE INDEX` statements for new tables.
   - Zero modifications, alterations, or column drops on existing tables (`users`, `student_profiles`, `coding_problems`, `assessments`, `job_opportunities`, `placement_drives`).
2. **Deterministic Downgrade Procedure:**
   - The Alembic migration script will include a verified, clean `downgrade()` function:
     ```python
     def downgrade():
         op.drop_table('user_notification_preferences')
         op.drop_table('user_notifications')
         op.drop_table('peer_study_group_members')
         op.drop_table('peer_study_groups')
         op.drop_table('peer_discussion_replies')
         op.drop_table('peer_discussion_threads')
         op.drop_table('mistake_notebook_entries')
         op.drop_table('student_card_reviews')
         op.drop_table('flashcard_items')
         op.drop_table('flashcard_decks')
     ```
   - Running `alembic downgrade -1` will safely remove only Phase 10 tables without touching Phase 0–9 data.
3. **Workspace Isolation:**
   - If an unexpected defect occurs during implementation, Git restoration will discard unstaged Phase 10 files without impacting previous commits.
