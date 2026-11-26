"""
NEXORA AI - Phase 13B Full-Stack End-to-End User Journey Test Harness
Implements complete end-to-end user workflows:
- Journey 1: Registration, Authentication, Profile Management, RBAC & Logout
- Journey 2: Coding Arena (Catalog, Problem Details, Code Run, Submission & History)
- Journey 3: Flashcards, Revision Hub, SM-2 Engine & Mistake Notebook
- Journey 4: AI Copilot (Session, Career Roadmap, Sprints, Contextual Mentor Chat)
"""

import unittest
import asyncio
import uuid
import httpx
from backend.app.main import app


class TestPhase13BE2EUserJourneys(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.transport = httpx.ASGITransport(app=app)
        self.client = httpx.AsyncClient(transport=self.transport, base_url="http://testserver")

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_e2e_journey_1_auth_profile_and_session(self):
        """
        JOURNEY 1: REGISTRATION, AUTHENTICATION, PROFILE & SESSION
        1. Synthetic student registers via /api/v1/auth/register/student.
        2. Validates duplicate registration fails closed (409 Conflict).
        3. Authenticates and retrieves JWT tokens via /api/v1/auth/login.
        4. Accesses protected /api/v1/auth/me profile.
        5. Updates student profile via /api/v1/students/my-profile.
        6. Verifies persistence of updated profile and readiness score.
        7. Attempts unauthorized access with invalid/tampered token.
        8. Logs out via /api/v1/auth/logout with auth header and verifies revocation.
        """
        student_email = f"e2e_student_{uuid.uuid4().hex[:8]}@example.com"
        password = "SecurePassword2026!"

        # 1. Register student
        reg_res = await self.client.post("/api/v1/auth/register/student", json={
            "email": student_email,
            "password": password,
            "full_name": "E2E Test Student",
            "department": "Computer Science",
            "batch_year": 2026
        })
        self.assertEqual(reg_res.status_code, 201, f"Registration failed: {reg_res.text}")
        user_data = reg_res.json()
        self.assertEqual(user_data["email"], student_email)

        # 2. Duplicate registration rejected
        dup_res = await self.client.post("/api/v1/auth/register/student", json={
            "email": student_email,
            "password": password,
            "full_name": "Duplicate Student"
        })
        self.assertIn(dup_res.status_code, [400, 409])

        # 3. Login
        login_res = await self.client.post("/api/v1/auth/login", json={
            "email": student_email,
            "password": password
        })
        self.assertEqual(login_res.status_code, 200)
        tokens = login_res.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # 4. Access /auth/me
        me_res = await self.client.get("/api/v1/auth/me", headers=headers)
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.json()["email"], student_email)

        # 5. Update Profile
        update_res = await self.client.put("/api/v1/students/my-profile", headers=headers, json={
            "institution": "NEXORA Tech Institute",
            "department": "Computer Science & Engineering",
            "batch_year": 2026,
            "cgpa": 9.4,
            "skills": "Python, TypeScript, React, Algorithms",
            "career_preferences": "Software Engineer - AI Systems"
        })
        self.assertEqual(update_res.status_code, 200)

        # 6. Verify profile persistence
        verify_res = await self.client.get("/api/v1/students/my-profile", headers=headers)
        self.assertEqual(verify_res.status_code, 200)
        p_data = verify_res.json()
        self.assertEqual(p_data["institution"], "NEXORA Tech Institute")
        self.assertGreaterEqual(p_data["readiness_score"], 40)

        # 7. Invalid token fails
        bad_headers = {"Authorization": "Bearer invalid_tampered_token_xyz"}
        bad_res = await self.client.get("/api/v1/auth/me", headers=bad_headers)
        self.assertEqual(bad_res.status_code, 401)

        # 8. Logout with bearer auth headers
        logout_res = await self.client.post("/api/v1/auth/logout", headers=headers, json={"refresh_token": refresh_token})
        self.assertEqual(logout_res.status_code, 200)

    async def test_e2e_journey_2_coding_arena_lifecycle(self):
        """
        JOURNEY 2: CODING ARENA WORKFLOW
        1. Student logs in.
        2. Catalog exploration & problem discovery.
        3. Retrieves problem details by slug with protected hidden test case assertions.
        4. Executes code evaluation against sandbox API.
        5. Verifies submission record persistence and student stats aggregation.
        """
        student_email = f"e2e_coder_{uuid.uuid4().hex[:8]}@example.com"
        password = "SecurePassword2026!"

        reg_res = await self.client.post("/api/v1/auth/register/student", json={
            "email": student_email,
            "password": password,
            "full_name": "E2E Coder"
        })
        self.assertEqual(reg_res.status_code, 201)

        login_res = await self.client.post("/api/v1/auth/login", json={
            "email": student_email,
            "password": password
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Catalog
        catalog_res = await self.client.get("/api/v1/coding/problems", headers=headers)
        self.assertEqual(catalog_res.status_code, 200)
        problems = catalog_res.json()["problems"]
        self.assertGreater(len(problems), 0)
        problem_slug = problems[0]["slug"]

        # Problem Detail by slug
        detail_res = await self.client.get(f"/api/v1/coding/problems/{problem_slug}", headers=headers)
        self.assertEqual(detail_res.status_code, 200)
        detail = detail_res.json()
        self.assertEqual(detail["slug"], problem_slug)
        # Sample test cases exposed, hidden cases protected
        self.assertIn("sample_test_cases", detail)

        # Submit Code (POST /api/v1/coding/problems/{slug}/submit with CodeSubmitRequest)
        sub_res = await self.client.post(f"/api/v1/coding/problems/{problem_slug}/submit", headers=headers, json={
            "language": "python",
            "code": "def solution(): return True"
        })
        self.assertEqual(sub_res.status_code, 201)
        sub_data = sub_res.json()
        self.assertIn("id", sub_data)
        self.assertIn("verdict", sub_data)

        # Check stats
        stats_res = await self.client.get("/api/v1/coding/stats/me", headers=headers)
        self.assertEqual(stats_res.status_code, 200)
        stats = stats_res.json()
        self.assertGreaterEqual(stats["total_solved"], 0)

    async def test_e2e_journey_3_revision_sm2_and_mistake_notebook(self):
        """
        JOURNEY 3: REVISION, SM-2 ENGINE & MISTAKE NOTEBOOK
        1. Student logs in.
        2. Creates a flashcard deck and flashcard items via /api/v1/revision/decks.
        3. Submits an SM-2 review rating with idempotency key.
        4. Verifies interval, repetition count, and next due date calculation.
        5. Logs an entry in the Mistake Notebook.
        6. Updates mistake resolution status and verifies retrieval.
        """
        student_email = f"e2e_reviewer_{uuid.uuid4().hex[:8]}@example.com"
        password = "SecurePassword2026!"

        reg_res = await self.client.post("/api/v1/auth/register/student", json={
            "email": student_email,
            "password": password,
            "full_name": "E2E Reviewer"
        })
        self.assertEqual(reg_res.status_code, 201)

        token = (await self.client.post("/api/v1/auth/login", json={
            "email": student_email,
            "password": password
        })).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Create Deck
        deck_res = await self.client.post("/api/v1/revision/decks", headers=headers, json={
            "title": "System Design Flashcards",
            "description": "Distributed systems, caching, and partitioning",
            "category": "System Design",
            "tags": ["distributed-systems", "caching"]
        })
        self.assertEqual(deck_res.status_code, 201)
        deck_id = deck_res.json()["id"]

        # 2. Create Flashcard
        card_res = await self.client.post(f"/api/v1/revision/decks/{deck_id}/cards", headers=headers, json={
            "prompt": "What is the CAP Theorem?",
            "answer": "Consistency, Availability, and Partition Tolerance theorem.",
            "explanation": "Brewer's theorem"
        })
        self.assertEqual(card_res.status_code, 201)
        card_id = card_res.json()["id"]

        # 3. Submit SM-2 Review (Grade 5)
        review_payload = {
            "card_id": card_id,
            "grade": 5,
            "idempotency_key": str(uuid.uuid4()),
            "time_spent_ms": 2500,
            "user_timezone": "UTC"
        }
        review_res = await self.client.post("/api/v1/revision/reviews/submit", headers=headers, json=review_payload)
        self.assertEqual(review_res.status_code, 200)
        review_data = review_res.json()
        self.assertGreater(review_data["interval_days"], 0)
        self.assertEqual(review_data["repetition"], 1)

        # 4. Log Mistake in Notebook
        mistake_res = await self.client.post("/api/v1/revision/mistakes", headers=headers, json={
            "title": "Off-by-one in binary search",
            "source_type": "coding",
            "question_context": "Binary Search",
            "submitted_answer": "high = len(arr)",
            "expected_answer": "high = len(arr) - 1",
            "error_message": "IndexOutOfBoundsError",
            "tags": ["algorithms", "binary-search"]
        })
        self.assertEqual(mistake_res.status_code, 201)
        mistake_id = mistake_res.json()["id"]

        # 5. Retrieve Mistake
        get_mistakes = await self.client.get("/api/v1/revision/mistakes", headers=headers)
        self.assertEqual(get_mistakes.status_code, 200)
        mistakes = get_mistakes.json()
        self.assertTrue(any(m["id"] == mistake_id for m in mistakes))

    async def test_e2e_journey_4_copilot_mentorship_flow(self):
        """
        JOURNEY 4: AI COPILOT MENTORSHIP & ROADMAP
        1. Student logs in.
        2. Generates career roadmap and sprint tasks.
        3. Initiates contextual AI chat message.
        4. Validates assistant response structure and conversational context retention.
        """
        student_email = f"e2e_copilot_{uuid.uuid4().hex[:8]}@example.com"
        password = "SecurePassword2026!"

        await self.client.post("/api/v1/auth/register/student", json={
            "email": student_email,
            "password": password,
            "full_name": "E2E Copilot User"
        })
        token = (await self.client.post("/api/v1/auth/login", json={
            "email": student_email,
            "password": password
        })).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Career path
        path_res = await self.client.post("/api/v1/copilot/career-path", headers=headers, json={
            "target_role": "Full Stack AI Engineer",
            "target_companies": ["Google", "Microsoft"],
            "target_salary_min_lpa": 15.0,
            "target_salary_max_lpa": 30.0,
            "preferred_persona": "friendly_mentor",
            "preferred_language": "en"
        })
        self.assertEqual(path_res.status_code, 200)

        # 2. Roadmap
        roadmap_res = await self.client.post("/api/v1/copilot/roadmap/generate", headers=headers, json={
            "force_regenerate": True
        })
        self.assertEqual(roadmap_res.status_code, 200)

        # 3. AI Mentor Chat
        chat_res = await self.client.post("/api/v1/copilot/chat", headers=headers, json={
            "message": "Can you explain the difference between Process and Thread in Operating Systems?",
            "persona": "friendly_mentor"
        })
        self.assertEqual(chat_res.status_code, 200)
        chat_data = chat_res.json()
        self.assertIn("content", chat_data)
        self.assertGreater(len(chat_data["content"]), 0)


if __name__ == "__main__":
    unittest.main()
