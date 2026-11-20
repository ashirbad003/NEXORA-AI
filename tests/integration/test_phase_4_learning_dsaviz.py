import unittest
import asyncio
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.db.session import Base
from backend.app.core.config import settings

class TestPhase4LearningAndDSAViz(unittest.IsolatedAsyncioTestCase):
    """
    Automated Test Suite for Phase 4:
    - Learning Hub & Interactive Concept Explorer (FEAT-123..FEAT-144)
    - DSA Visualizer Step-by-Step Simulation (FEAT-163..FEAT-180)
    - Student Topic Progress Tracking & Mastery (FEAT-128)
    - Student Personal Notes & Bookmarks (FEAT-141)
    - Multi-Parameter Topic Search & Difficulty Filters (FEAT-134, FEAT-135)
    - AI Concept Tutor Socratic Mode (FEAT-126)
    - Client-Safe Code Snippet AST Sandbox (FEAT-127)
    - Curated Video Resources (FEAT-130)
    - Practice Problems Embedder (FEAT-131)
    - Downloadable Concept Cheat Sheets (FEAT-132)
    - Multilingual Learning Content (FEAT-133)
    - Topic Difficulty Feedback & Confusing Sections (FEAT-135)
    - Real-World Architecture Case Studies (FEAT-137)
    - Interactive Flash Quiz Checkpoints (FEAT-138)
    - Curriculum Versioning & Changelog (FEAT-144)
    """

    async def asyncSetUp(self):
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.AsyncSessionLocal = async_sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        from backend.app.db.session import get_db_session
        async def override_get_db_session():
            async with self.AsyncSessionLocal() as session:
                yield session

        app.dependency_overrides[get_db_session] = override_get_db_session
        self.transport = ASGITransport(app=app)
        self.base_url = "http://testserver"

    async def asyncTearDown(self):
        from backend.app.db.session import get_db_session
        app.dependency_overrides.clear()
        await self.engine.dispose()

    async def _get_auth_headers(self, client: AsyncClient) -> dict:
        await client.post("/api/v1/auth/register/student", json={
            "email": "learner@nexora.ai",
            "password": "Password123!",
            "full_name": "Active Learner"
        })
        login = await client.post("/api/v1/auth/login", json={
            "email": "learner@nexora.ai",
            "password": "Password123!"
        })
        token = login.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    async def test_01_list_learning_modules_and_seeding(self):
        """Verify curriculum modules listing, auto-seeding, and category filtering (FEAT-123..FEAT-125)."""
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            resp = await client.get("/api/v1/learn/modules")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertGreaterEqual(data["total"], 4)
            self.assertTrue(any(m["slug"] == "arrays-and-hashing" for m in data["modules"]))

            # Filter by category
            dsa_resp = await client.get("/api/v1/learn/modules?category=DSA")
            self.assertEqual(dsa_resp.status_code, 200)
            dsa_data = dsa_resp.json()
            self.assertTrue(all(m["category"] == "DSA" for m in dsa_data["modules"]))

    async def test_02_get_learning_module_by_slug(self):
        """Verify individual concept module fetch with rich markdown content (FEAT-123, FEAT-125)."""
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            resp = await client.get("/api/v1/learn/modules/graph-traversal-bfs-dfs")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["slug"], "graph-traversal-bfs-dfs")
            self.assertEqual(data["difficulty_level"], "Medium")
            self.assertIn("# Graph Traversals", data["content_markdown"])

    async def test_03_student_topic_progress_and_mastery(self):
        """Verify recording student topic mastery and fetching progress summary (FEAT-128, FEAT-129)."""
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            headers = await self._get_auth_headers(client)

            # Record progress on arrays-and-hashing
            prog_resp = await client.post(
                "/api/v1/learn/modules/arrays-and-hashing/progress",
                json={"is_completed": True, "mastery_score": 95},
                headers=headers
            )
            self.assertEqual(prog_resp.status_code, 200)
            prog_data = prog_resp.json()
            self.assertTrue(prog_data["is_completed"])
            self.assertEqual(prog_data["mastery_score"], 95)

            # Fetch my progress
            my_prog = await client.get("/api/v1/learn/progress/me", headers=headers)
            self.assertEqual(my_prog.status_code, 200)
            self.assertEqual(len(my_prog.json()), 1)

    async def test_04_student_personal_notes_and_bookmarks(self):
        """Verify adding personal notes and bookmarks anchored to learning modules (FEAT-136, FEAT-139)."""
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            headers = await self._get_auth_headers(client)

            # Post a note
            note_resp = await client.post(
                "/api/v1/learn/modules/arrays-and-hashing/notes",
                json={"note_content": "Remember amortized resizing happens at 2x capacity.", "is_bookmarked": True},
                headers=headers
            )
            self.assertEqual(note_resp.status_code, 201)
            note_data = note_resp.json()
            self.assertTrue(note_data["is_bookmarked"])
            self.assertIn("amortized resizing", note_data["note_content"])

            # Retrieve notes
            notes_get = await client.get("/api/v1/learn/modules/arrays-and-hashing/notes", headers=headers)
            self.assertEqual(notes_get.status_code, 200)
            self.assertEqual(len(notes_get.json()), 1)

    async def test_05_dsa_visualizer_bfs_simulation(self):
        """Verify BFS step-by-step animation queue simulation (FEAT-163, FEAT-164, FEAT-165)."""
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            payload = {
                "algorithm": "bfs",
                "nodes": ["A", "B", "C", "D"],
                "edges": [["A", "B"], ["A", "C"], ["B", "D"]],
                "start_node": "A"
            }
            resp = await client.post("/api/v1/dsaviz/simulate/traversal", json=payload)
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["algorithm"], "BFS")
            self.assertGreater(data["total_steps"], 1)
            self.assertEqual(data["result"]["traversal_order"], ["A", "B", "C", "D"])
            self.assertIn("queue", data["steps"][0]["state_snapshot"])

    async def test_06_dsa_visualizer_dfs_simulation(self):
        """Verify DFS step-by-step stack/backtracking animation trace (FEAT-172)."""
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            payload = {
                "algorithm": "dfs",
                "nodes": ["A", "B", "C", "D"],
                "edges": [["A", "B"], ["B", "C"], ["C", "D"]],
                "start_node": "A"
            }
            resp = await client.post("/api/v1/dsaviz/simulate/traversal", json=payload)
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["algorithm"], "DFS")
            self.assertIn("stack", data["steps"][0]["state_snapshot"])

    async def test_07_dsa_visualizer_dijkstra_simulation(self):
        """Verify Dijkstra priority queue & distance table updates (FEAT-179)."""
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            payload = {
                "algorithm": "dijkstra",
                "nodes": ["A", "B", "C"],
                "edges": [
                    {"from": "A", "to": "B", "weight": 2},
                    {"from": "B", "to": "C", "weight": 3},
                    {"from": "A", "to": "C", "weight": 10}
                ],
                "start_node": "A"
            }
            resp = await client.post("/api/v1/dsaviz/simulate/shortest-path", json=payload)
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["algorithm"], "Dijkstra")
            self.assertEqual(data["result"]["shortest_distances"]["C"], 5.0)

    async def test_08_dsa_visualizer_knapsack_dp_simulation(self):
        """Verify 0/1 Knapsack 2D DP matrix animation calculation (FEAT-180)."""
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            resp = await client.get("/api/v1/dsaviz/simulate/knapsack?capacity=7")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["algorithm"], "0/1 Knapsack DP")
            self.assertGreater(data["total_steps"], 10)
            self.assertGreater(data["result"]["max_value"], 0)

    # --- TESTS FOR 11 COMPLETED PHASE 4 FEATURES ---

    async def test_09_multi_parameter_search_and_difficulty_filter(self):
        """Verify topic search (FEAT-134) and difficulty level filter (FEAT-135)."""
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            # Multi-parameter: category=DSA & difficulty=Easy
            resp = await client.get("/api/v1/learn/modules?category=DSA&difficulty=Easy")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertTrue(all(m["difficulty_level"] == "Easy" for m in data["modules"]))

            # Text search query (FEAT-134)
            search_resp = await client.get("/api/v1/learn/modules?search=concurrency")
            self.assertEqual(search_resp.status_code, 200)
            s_data = search_resp.json()
            self.assertGreaterEqual(s_data["total"], 1)
            self.assertIn("concurrency", s_data["modules"][0]["slug"])

    async def test_10_ai_concept_tutor_socratic_mode(self):
        """Verify Socratic AI guidance endpoint with focus areas (FEAT-126)."""
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            headers = await self._get_auth_headers(client)
            payload = {
                "concept_slug": "graph-traversal-bfs-dfs",
                "student_query": "Why does BFS use a queue while DFS uses a stack?"
            }
            resp = await client.post("/api/v1/learn/socratic-tutor", json=payload, headers=headers)
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["concept_slug"], "graph-traversal-bfs-dfs")
            self.assertIn("FIFO", data["guiding_question"])
            self.assertGreater(len(data["suggested_focus_areas"]), 0)

    async def test_11_interactive_code_snippet_sandbox_ast_safety(self):
        """Verify client-safe AST sandbox execution and dangerous call blocking (FEAT-127)."""
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            headers = await self._get_auth_headers(client)

            # Safe code execution
            safe_payload = {
                "language": "python",
                "code": "def binary_search(arr, t):\n    l, r = 0, len(arr) - 1\n    return -1"
            }
            resp = await client.post("/api/v1/learn/snippet-sandbox", json=safe_payload, headers=headers)
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertEqual(data["status"], "success")
            self.assertTrue(data["ast_analysis"]["security_safe"])
            self.assertIn("binary_search", data["ast_analysis"]["functions"])

            # Prohibited code execution blocked
            danger_payload = {
                "language": "python",
                "code": "import os\nos.system('echo dangerous')"
            }
            danger_resp = await client.post("/api/v1/learn/snippet-sandbox", json=danger_payload, headers=headers)
            self.assertEqual(danger_resp.status_code, 200)
            d_data = danger_resp.json()
            self.assertEqual(d_data["status"], "security_blocked")
            self.assertFalse(d_data["ast_analysis"]["security_safe"])

    async def test_12_video_resource_curator(self):
        """Verify curated high-quality free video lectures and animations (FEAT-130)."""
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            resp = await client.get("/api/v1/learn/modules/arrays-and-hashing/resources")
            self.assertEqual(resp.status_code, 200)
            resources = resp.json()
            self.assertGreater(len(resources), 0)
            self.assertIn("Memory Allocation", resources[0]["title"])
            self.assertTrue(resources[0]["embed_url"].startswith("http"))

    async def test_13_practice_problem_embedder(self):
        """Verify links to relevant Coding Arena questions (FEAT-131)."""
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            resp = await client.get("/api/v1/learn/modules/arrays-and-hashing/problems")
            self.assertEqual(resp.status_code, 200)
            problems = resp.json()
            self.assertGreater(len(problems), 0)
            self.assertTrue(any(p["coding_arena_slug"] == "two-sum" for p in problems))

    async def test_14_downloadable_concept_cheat_sheets(self):
        """Verify high-yield one-page summary cheat sheet generation (FEAT-132)."""
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            resp = await client.get("/api/v1/learn/modules/arrays-and-hashing/cheat-sheet")
            self.assertEqual(resp.status_code, 200)
            sheet = resp.json()
            self.assertEqual(sheet["slug"], "arrays-and-hashing")
            self.assertIn("O(1)", str(sheet["complexity_table"]))
            self.assertGreater(len(sheet["key_takeaways"]), 1)
            self.assertIn("prefix", sheet["code_reference"])

    async def test_15_multilingual_learning_language_selector(self):
        """Verify notes translated into Hindi and regional languages (FEAT-133)."""
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            resp = await client.get("/api/v1/learn/modules/arrays-and-hashing/translate?lang=hi")
            self.assertEqual(resp.status_code, 200)
            trans = resp.json()
            self.assertEqual(trans["language"], "hi")
            self.assertIn("ऐरे", trans["title"])

    async def test_16_topic_difficulty_feedback(self):
        """Verify student difficulty rating and confusing section submission (FEAT-135)."""
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            headers = await self._get_auth_headers(client)
            payload = {
                "difficulty_rating": 4,
                "confusing_sections": "Amortized resizing proof and geometric series bound.",
                "feedback_text": "Need more visual charts for memory doubling."
            }
            resp = await client.post(
                "/api/v1/learn/modules/arrays-and-hashing/feedback",
                json=payload,
                headers=headers
            )
            self.assertEqual(resp.status_code, 201)
            f_data = resp.json()
            self.assertEqual(f_data["difficulty_rating"], 4)
            self.assertIn("Amortized resizing", f_data["confusing_sections"])

    async def test_17_real_world_architecture_case_studies(self):
        """Verify deep dives into Netflix, Uber, and WhatsApp architectures (FEAT-137)."""
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            resp = await client.get("/api/v1/learn/case-studies")
            self.assertEqual(resp.status_code, 200)
            studies = resp.json()
            self.assertEqual(len(studies), 3)
            names = [s["system_name"] for s in studies]
            self.assertIn("Netflix", names)
            self.assertIn("Uber", names)
            self.assertIn("WhatsApp", names)

    async def test_18_interactive_flash_quiz_checkpoints(self):
        """Verify 2-minute checkpoints interspersed within reading material (FEAT-138)."""
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            headers = await self._get_auth_headers(client)
            # Fetch quiz
            q_resp = await client.get("/api/v1/learn/modules/arrays-and-hashing/quiz")
            self.assertEqual(q_resp.status_code, 200)
            quiz = q_resp.json()
            self.assertGreater(len(quiz["questions"]), 0)

            # Submit answers
            sub_resp = await client.post(
                "/api/v1/learn/modules/arrays-and-hashing/quiz/submit",
                json={"answers": {"q1": 2, "q2": 1}},
                headers=headers
            )
            self.assertEqual(sub_resp.status_code, 200)
            res_data = sub_resp.json()
            self.assertEqual(res_data["score"], 2)
            self.assertTrue(res_data["passed"])
            self.assertEqual(res_data["percentage"], 100.0)

    async def test_19_curriculum_versioning_and_changelog(self):
        """Verify curriculum note updates and historical revision diffs (FEAT-144)."""
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as client:
            resp = await client.get("/api/v1/learn/changelog")
            self.assertEqual(resp.status_code, 200)
            log = resp.json()
            self.assertGreater(len(log), 0)
            self.assertEqual(log[0]["version"], "v1.4.0")
            self.assertIn("arrays-and-hashing", log[0]["affected_topics"])
