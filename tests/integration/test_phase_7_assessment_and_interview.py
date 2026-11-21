import unittest
import os
import sys
import httpx
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from backend.app.db.session import Base, get_db_session
from backend.app.models.auth import User, Role, StudentProfile
from backend.app.core.security import hash_password, create_access_token
from backend.app.schemas.user import UserRoleEnum
from backend.app.main import app

TEST_DB_URL = "sqlite+aiosqlite:///./test_phase7_suite.db"

class TestPhase7AssessmentAndInterview(unittest.IsolatedAsyncioTestCase):
    """
    Integration tests covering Phase 7 (FEAT-041 to FEAT-062 & FEAT-103 to FEAT-122):
    - Timed assessment engine with auto-save & recovery
    - Question shuffling & negative marking evaluator
    - Sectional time limits & diagnostic scorecard
    - Window blur detection & public leaderboard
    - AI Mock Interview Studio with dynamic follow-up
    - STAR methodology scorer & tone/clarity analyzer
    - System design whiteboard mode & readiness scorecard
    """

    async def asyncSetUp(self):
        self.engine = create_async_engine(TEST_DB_URL, echo=False)
        self.AsyncSessionLocal = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

        async def override_get_db_session():
            async with self.AsyncSessionLocal() as session:
                try:
                    yield session
                except Exception:
                    await session.rollback()
                    raise
                finally:
                    await session.close()

        app.dependency_overrides[get_db_session] = override_get_db_session
        self.transport = httpx.ASGITransport(app=app)
        self.client = httpx.AsyncClient(transport=self.transport, base_url="http://testserver")

        self.test_user_id = "test-student-phase7-id"

        # Seed roles & student user
        async with self.AsyncSessionLocal() as session:
            student_role = Role(id="role_student_p7", name=UserRoleEnum.STUDENT.value, description="Student")
            session.add(student_role)

            user = User(
                id=self.test_user_id,
                email="student.phase7@nexora.ai",
                hashed_password=hash_password("Password123!"),
                full_name="Phase 7 Student",
                is_active=True,
            )
            user.roles.append(student_role)
            session.add(user)

            profile = StudentProfile(
                user_id=self.test_user_id,
                institution="National Institute of Technology",
                department="Computer Science",
                batch_year="2026",
                cgpa=8.8,
                career_preferences="FullStack Engineer",
                skills="Python, SQL, FastApi, React"
            )
            session.add(profile)
            await session.commit()

        self.auth_token = create_access_token(
            subject=self.test_user_id,
            role="STUDENT",
        )
        self.headers = {"Authorization": f"Bearer {self.auth_token}"}

    async def asyncTearDown(self):
        await self.client.aclose()
        await self.engine.dispose()
        if os.path.exists("./test_phase7_suite.db"):
            try:
                os.remove("./test_phase7_suite.db")
            except Exception:
                pass

    async def test_01_create_and_list_assessment(self):
        # 1. Admin creates assessment with questions (FEAT-058, FEAT-059)
        create_payload = {
            "title": "Full-Stack Diagnostic Test",
            "description": "Tests OS, DBMS and Algorithms",
            "category": "Technical",
            "difficulty": "Medium",
            "duration_minutes": 20,
            "total_marks": 20.0,
            "pass_marks": 10.0,
            "negative_marking_rate": 0.25,
            "retake_allowed": True,
            "company_template": "Amazon",
            "questions": [
                {
                    "section_name": "Core CS",
                    "order_index": 0,
                    "question_text": "Which normal form eliminates transitive dependency?",
                    "options": {"A": "1NF", "B": "2NF", "C": "3NF", "D": "BCNF"},
                    "correct_option": "C",
                    "marks": 2.0,
                    "explanation": "3NF removes transitive dependencies where non-prime attributes depend on other non-prime attributes.",
                    "topic_tag": "DBMS",
                    "difficulty": "Medium"
                },
                {
                    "section_name": "Algorithms",
                    "order_index": 1,
                    "question_text": "What is the worst-case time complexity of Quicksort?",
                    "options": {"A": "O(N)", "B": "O(N log N)", "C": "O(N^2)", "D": "O(log N)"},
                    "correct_option": "C",
                    "marks": 2.0,
                    "explanation": "Quicksort degrades to O(N^2) when poor pivots are chosen.",
                    "topic_tag": "Algorithms",
                    "difficulty": "Easy"
                }
            ]
        }
        res = await self.client.post("/api/v1/assessments/tests", json=create_payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        test_id = res.json()["test_id"]
        self.assertTrue(test_id)

        # 2. List published tests (FEAT-051, FEAT-052)
        list_res = await self.client.get("/api/v1/assessments/tests", headers=self.headers)
        self.assertEqual(list_res.status_code, 200)
        tests = list_res.json()
        self.assertTrue(any(t["id"] == test_id for t in tests))

    async def test_02_assessment_attempt_lifecycle_and_scoring(self):
        # Create test
        test_payload = {
            "title": "Operating Systems Quiz",
            "duration_minutes": 15,
            "total_marks": 4.0,
            "negative_marking_rate": 0.5,
            "questions": [
                {
                    "section_name": "OS",
                    "question_text": "Which scheduling algorithm avoids starvation?",
                    "options": {"A": "FCFS", "B": "Round Robin", "C": "SJF", "D": "Priority"},
                    "correct_option": "B",
                    "marks": 2.0,
                    "topic_tag": "Operating Systems"
                },
                {
                    "section_name": "OS",
                    "question_text": "What is thrashing?",
                    "options": {"A": "High CPU utilization", "B": "Excessive page swapping", "C": "Deadlock", "D": "Memory leak"},
                    "correct_option": "B",
                    "marks": 2.0,
                    "topic_tag": "Memory Management"
                }
            ]
        }
        c_res = await self.client.post("/api/v1/assessments/tests", json=test_payload, headers=self.headers)
        test_id = c_res.json()["test_id"]

        # 1. Start Attempt (FEAT-041: Timed core & FEAT-044: Randomization)
        start_res = await self.client.post(f"/api/v1/assessments/tests/{test_id}/start", headers=self.headers)
        self.assertEqual(start_res.status_code, 200)
        data = start_res.json()
        attempt_id = data["attempt_id"]
        questions = data["shuffled_questions"]
        self.assertEqual(len(questions), 2)
        self.assertGreater(data["remaining_seconds"], 0)

        # 2. Auto-save Answer Batch & Blur Event (FEAT-042: Auto-Save & FEAT-053: Anti-cheating blur)
        # In questions, find which question has topic 'Memory Management'
        mem_q = next(q for q in questions if q["topic_tag"] == "Memory Management")
        os_q = next(q for q in questions if q["topic_tag"] == "Operating Systems")

        save_payload = {
            "answers": [
                {"question_id": os_q["id"], "selected_option": "B", "time_spent_seconds": 25},  # Correct
                {"question_id": mem_q["id"], "selected_option": "A", "time_spent_seconds": 15}  # Incorrect option (A instead of B)
            ],
            "blur_count": 1,
            "flagged_question_ids": [mem_q["id"]]
        }
        save_res = await self.client.put(f"/api/v1/assessments/attempts/{attempt_id}/save", json=save_payload, headers=self.headers)
        self.assertEqual(save_res.status_code, 200)
        self.assertEqual(save_res.json()["status"], "saved")

        # 3. Submit Attempt (FEAT-045: Negative Marking & FEAT-048: Scorecard & FEAT-055: Weak area extractor)
        submit_res = await self.client.post(f"/api/v1/assessments/attempts/{attempt_id}/submit", headers=self.headers)
        self.assertEqual(submit_res.status_code, 200)
        scorecard = submit_res.json()
        self.assertEqual(scorecard["correct_count"], 1)
        self.assertEqual(scorecard["incorrect_count"], 1)
        # Score = +2.0 (correct) - 0.5 (negative) = 1.5
        self.assertAlmostEqual(scorecard["score"], 1.5, places=1)
        self.assertIn("Memory Management", scorecard["weak_topic_tags"])

        # 4. Verify Leaderboard (FEAT-056)
        lead_res = await self.client.get(f"/api/v1/assessments/leaderboard/{test_id}", headers=self.headers)
        self.assertEqual(lead_res.status_code, 200)
        self.assertTrue(len(lead_res.json()) >= 1)

    async def test_03_mock_interview_studio_flow(self):
        # 1. Start AI Mock Interview Session (FEAT-103, FEAT-107, FEAT-109)
        start_payload = {
            "role_target": "Backend Engineer",
            "interview_type": "Technical",
            "company_persona": "Google"
        }
        res = await self.client.post("/api/v1/interview/start", json=start_payload, headers=self.headers)
        self.assertEqual(res.status_code, 200)
        session_data = res.json()
        session_id = session_data["session_id"]
        first_turn = session_data["current_turn"]
        self.assertEqual(first_turn["turn_index"], 1)
        self.assertTrue(first_turn["question_text"])

        # 2. Respond to Turn 1 (FEAT-106: Text Fallback & FEAT-118: Pacing Coach)
        resp_payload = {
            "response_text": (
                "When designing high-concurrency systems, optimistic locking works best when contention is rare by using "
                "a version field, whereas pessimistic locking uses SELECT FOR UPDATE to prevent race conditions on shared database rows."
            ),
            "audio_duration_seconds": 45
        }
        respond_res = await self.client.post(f"/api/v1/interview/sessions/{session_id}/respond", json=resp_payload, headers=self.headers)
        self.assertEqual(respond_res.status_code, 200)
        turn_data = respond_res.json()
        self.assertEqual(turn_data["pacing_verdict"], "Optimal")
        self.assertTrue(turn_data["previous_feedback"])

        # 3. Complete Turns up to Evaluation (FEAT-110, FEAT-111, FEAT-112, FEAT-113, FEAT-117, FEAT-120)
        resp_payload_2 = {
            "response_text": (
                "In my previous project, we faced a situation where Redis cache latency spiked. My task was to optimize the read replica pool. "
                "I implemented connection pooling with asynchronous pipelines, which resulted in a 45 percent latency reduction."
            ),
            "audio_duration_seconds": 60,
            "whiteboard_snapshot": {"elements": [{"type": "box", "label": "Redis Cache"}]}
        }
        await self.client.post(f"/api/v1/interview/sessions/{session_id}/respond", json=resp_payload_2, headers=self.headers)
        await self.client.post(f"/api/v1/interview/sessions/{session_id}/respond", json=resp_payload_2, headers=self.headers)

        eval_res = await self.client.get(f"/api/v1/interview/sessions/{session_id}/evaluation", headers=self.headers)
        self.assertEqual(eval_res.status_code, 200)
        eval_data = eval_res.json()
        self.assertGreater(eval_data["overall_readiness_score"], 0)
        self.assertIn("situation", eval_data["star_scores"])
        self.assertIn("focus_areas", eval_data["improvement_plan"])
        self.assertTrue(len(eval_data["transcript"]) >= 2)
