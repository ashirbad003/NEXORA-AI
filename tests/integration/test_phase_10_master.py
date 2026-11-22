import unittest
import os
import sys
import asyncio
import uuid
import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.main import app
from backend.app.services.sm2_service import SM2Engine
from backend.app.services.scheduler_service import NotificationScheduler
from backend.app.models.phase10_revision import FlashcardDeck, FlashcardItem, StudentCardReview
from backend.app.models.phase10_peer import PeerDiscussionThread, PeerDiscussionReply, PeerStudyGroup
from backend.app.models.phase10_notifications import UserNotification
from backend.app.models.auth import User, Role
from backend.app.core.security import hash_password, create_access_token
from backend.app.db.session import AsyncSessionLocal

class TestPhase10Master(unittest.IsolatedAsyncioTestCase):

    def test_01_sm2_mathematical_engine(self):
        # Initial review: Grade 5 (Perfect)
        res1 = SM2Engine.calculate(0, 0, 2.50, 1.0, 5)
        self.assertEqual(res1.repetition, 1)
        self.assertEqual(res1.interval_days, 1)
        self.assertEqual(res1.ease_factor, 2.60)
        self.assertGreater(res1.stability, 1.0)

        # Second review: Grade 4 (Good)
        res2 = SM2Engine.calculate(res1.repetition, res1.interval_days, res1.ease_factor, res1.stability, 4)
        self.assertEqual(res2.repetition, 2)
        self.assertEqual(res2.interval_days, 6)
        self.assertEqual(res2.ease_factor, 2.60)

        # Third review: Grade 5
        res3 = SM2Engine.calculate(res2.repetition, res2.interval_days, res2.ease_factor, res2.stability, 5)
        self.assertEqual(res3.repetition, 3)
        self.assertGreaterEqual(res3.interval_days, 15)
        self.assertEqual(res3.ease_factor, 2.70)

        # Lapse: Grade 1 (Failure)
        res_fail = SM2Engine.calculate(res3.repetition, res3.interval_days, res3.ease_factor, res3.stability, 1)
        self.assertEqual(res_fail.repetition, 0)
        self.assertEqual(res_fail.interval_days, 1)
        self.assertLess(res_fail.ease_factor, res3.ease_factor)
        self.assertGreaterEqual(res_fail.ease_factor, 1.30)
        self.assertLessEqual(res_fail.stability, res3.stability)

    async def test_02_phase_10_api_endpoints_and_remediations(self):
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            from backend.app.services.auth_service import AuthService
            role_admin = await AuthService.get_or_create_role(db, "ADMIN")
            role_student = await AuthService.get_or_create_role(db, "STUDENT")

            # 1. Create student test user
            student_email = f"student_p10_{uuid.uuid4().hex[:8]}@example.com"
            u_student = User(
                email=student_email,
                full_name="Phase 10 Student",
                hashed_password=hash_password("password123"),
                is_active=True,
                is_email_verified=True,
                roles=[role_student]
            )
            # 2. Create peer test user (to test upvoting)
            peer_email = f"peer_p10_{uuid.uuid4().hex[:8]}@example.com"
            u_peer = User(
                email=peer_email,
                full_name="Phase 10 Peer",
                hashed_password=hash_password("password123"),
                is_active=True,
                is_email_verified=True,
                roles=[role_student]
            )
            # 3. Create admin test user
            admin_email = f"admin_p10_{uuid.uuid4().hex[:8]}@example.com"
            u_admin = User(
                email=admin_email,
                full_name="Phase 10 Admin",
                hashed_password=hash_password("password123"),
                is_active=True,
                is_email_verified=True,
                roles=[role_admin]
            )
            db.add_all([u_student, u_peer, u_admin])
            await db.commit()
            await db.refresh(u_student)
            await db.refresh(u_peer)
            await db.refresh(u_admin)
            student_id = u_student.id
            peer_id = u_peer.id
            admin_id = u_admin.id

        token_student = create_access_token(subject=student_id, role="STUDENT")
        headers_student = {"Authorization": f"Bearer {token_student}"}

        token_peer = create_access_token(subject=peer_id, role="STUDENT")
        headers_peer = {"Authorization": f"Bearer {token_peer}"}

        token_admin = create_access_token(subject=admin_id, role="ADMIN")
        headers_admin = {"Authorization": f"Bearer {token_admin}"}

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            # --- Flashcard Deck & Anki Import/Export ---
            deck_resp = await client.post(
                "/api/v1/revision/decks",
                headers=headers_student,
                json={
                    "title": "Data Structures Mastery",
                    "description": "Essential trees, heaps and graphs",
                    "category": "DSA",
                    "tags": ["tree", "graph"],
                    "is_public": True
                }
            )
            self.assertEqual(deck_resp.status_code, 201)
            deck_data = deck_resp.json()
            deck_id = deck_data["id"]

            # Add Flashcard Item
            card_resp = await client.post(
                f"/api/v1/revision/decks/{deck_id}/cards",
                headers=headers_student,
                json={
                    "prompt": "What is the time complexity of searching in a Balanced BST?",
                    "answer": "O(log N)",
                    "explanation": "Because height is bounded by log2(N)",
                    "order_index": 1
                }
            )
            self.assertEqual(card_resp.status_code, 201)
            card_id = card_resp.json()["id"]

            # FEAT-158: Anki Export
            export_resp = await client.get(f"/api/v1/revision/decks/{deck_id}/export/anki", headers=headers_student)
            self.assertEqual(export_resp.status_code, 200)
            export_json = export_resp.json()
            self.assertEqual(export_json["deck_title"], "Data Structures Mastery")
            self.assertEqual(len(export_json["cards"]), 1)

            # FEAT-157: Anki Import
            import_resp = await client.post(
                "/api/v1/revision/decks/import/anki",
                headers=headers_student,
                json={
                    "title": "Imported System Design Deck",
                    "category": "System Design",
                    "cards": [
                        {"prompt": "What is PACELC theorem?", "answer": "Partition tolerance, Availability, Consistency, Else Latency, Consistency"}
                    ]
                }
            )
            self.assertEqual(import_resp.status_code, 200)
            self.assertEqual(import_resp.json()["title"], "Imported System Design Deck")

            # FEAT-162: Admin Deck Moderation
            # Non-admin rejected with 403
            student_mod_resp = await client.get("/api/v1/revision/admin/moderation/pending", headers=headers_student)
            self.assertEqual(student_mod_resp.status_code, 403)

            # Admin lists pending decks
            admin_list_resp = await client.get("/api/v1/revision/admin/moderation/pending", headers=headers_admin)
            self.assertEqual(admin_list_resp.status_code, 200)

            # Admin approves deck
            admin_appr_resp = await client.post(f"/api/v1/revision/admin/moderation/{deck_id}/approve", headers=headers_admin)
            self.assertEqual(admin_appr_resp.status_code, 200)
            self.assertTrue(admin_appr_resp.json()["is_approved"])

            # FEAT-161: Deck Forking (by peer) after deck is approved
            fork_resp = await client.post(f"/api/v1/revision/decks/{deck_id}/fork", headers=headers_peer)
            self.assertEqual(fork_resp.status_code, 201)
            forked_data = fork_resp.json()
            self.assertEqual(forked_data["user_id"], peer_id)
            self.assertIn("Forked", forked_data["title"])

            # --- Review Card (Idempotent submission & hash check) ---
            idem_key = str(uuid.uuid4())
            review_payload = {
                "card_id": card_id,
                "grade": 5,
                "idempotency_key": idem_key,
                "time_spent_ms": 3200,
                "user_timezone": "UTC"
            }
            review_resp1 = await client.post("/api/v1/revision/reviews/submit", headers=headers_student, json=review_payload)
            self.assertEqual(review_resp1.status_code, 200)
            r1_data = review_resp1.json()
            self.assertFalse(r1_data["is_replayed"])
            self.assertEqual(r1_data["repetition"], 1)

            # Replay identical review request (Safe idempotency replay)
            review_resp2 = await client.post("/api/v1/revision/reviews/submit", headers=headers_student, json=review_payload)
            self.assertEqual(review_resp2.status_code, 200)
            r2_data = review_resp2.json()
            self.assertTrue(r2_data["is_replayed"])
            self.assertEqual(r2_data["repetition"], r1_data["repetition"])

            # Same idempotency key with conflicting grade -> HTTP 409
            conflict_payload = dict(review_payload)
            conflict_payload["grade"] = 1
            review_resp_conflict = await client.post("/api/v1/revision/reviews/submit", headers=headers_student, json=conflict_payload)
            self.assertEqual(review_resp_conflict.status_code, 409)

            # --- Peer Learning & Community: Author Self-Upvote Remediated ---
            thread_resp = await client.post(
                "/api/v1/community/threads",
                headers=headers_student,
                json={
                    "title": "How to handle Dijkstra with negative edges?",
                    "content": "Does Bellman-Ford work better for negative edge cycles?",
                    "category": "Algorithms",
                    "context_type": "topic"
                }
            )
            self.assertEqual(thread_resp.status_code, 201)
            thread_id = thread_resp.json()["id"]

            # Author self-upvote MUST fail with 400 (FEAT-280 Remediated)
            self_upvote = await client.post(f"/api/v1/community/threads/{thread_id}/upvote", headers=headers_student)
            self.assertEqual(self_upvote.status_code, 400)
            self.assertIn('cannot upvote', self_upvote.json()['detail'].lower())

            # Peer upvote succeeds
            peer_upvote = await client.post(f"/api/v1/community/threads/{thread_id}/upvote", headers=headers_peer)
            self.assertEqual(peer_upvote.status_code, 200)
            self.assertEqual(peer_upvote.json()["upvotes"], 1)

            # Peer replies
            reply_resp = await client.post(
                f"/api/v1/community/threads/{thread_id}/replies",
                headers=headers_peer,
                json={
                    "content": "Dijkstra fails with negative weights because visited nodes are assumed finalized. Use Bellman-Ford.",
                    "code_snippet": "for i in range(V-1):\n    for u, v, w in edges:\n        relax(u, v, w)"
                }
            )
            self.assertEqual(reply_resp.status_code, 201)
            reply_id = reply_resp.json()["id"]

            # Author accepts reply
            accept_resp = await client.post(
                f"/api/v1/community/threads/{thread_id}/replies/{reply_id}/accept",
                headers=headers_student
            )
            self.assertEqual(accept_resp.status_code, 200)

            # --- Scheduler Execution Verification ---
            # Execute single scheduler pass manually in test environment
            scheduler = NotificationScheduler(check_interval_seconds=60)
            async with AsyncSessionLocal() as db_sched:
                await scheduler.run_scheduled_tasks()
            # Verify no exceptions raised during scheduler execution cycle
            self.assertTrue(True)
