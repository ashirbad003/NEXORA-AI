from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional, Dict, Any

from backend.app.db.session import get_db_session
from backend.app.api.deps import get_current_user, require_roles
from backend.app.models.auth import User
from backend.app.models.learning import (
    LearningModule, StudentTopicProgress, StudentTopicNote, TopicFeedback
)
from backend.app.schemas.user import UserRoleEnum
from backend.app.schemas.learning import (
    LearningModuleResponse, LearningModuleListResponse,
    TopicProgressUpdate, TopicProgressResponse,
    TopicNoteCreate, TopicNoteResponse,
    GraphTraversalRequest, ShortestPathRequest, AlgorithmTraceResponse,
    SocraticTutorRequest, SocraticTutorResponse,
    CodeSnippetSimRequest, CodeSnippetSimResponse,
    VisualResource, PracticeProblem, CheatSheetResponse, MultilingualContentResponse,
    TopicFeedbackCreate, TopicFeedbackResponse,
    ArchitectureCaseStudy, FlashQuizResponse, FlashQuizSubmitRequest, FlashQuizResultResponse,
    CurriculumChangelogEntry
)
from backend.app.services.algorithm_service import AlgorithmTraceEngine
from backend.app.services.learning_service import LearningService

router = APIRouter(tags=["Learning & DSA Visualization"])

# Seed curriculum data generator helper
DEFAULT_MODULES = [
    {
        "slug": "arrays-and-hashing",
        "title": "Arrays & Dynamic Hashing",
        "category": "DSA",
        "summary": "Core array operations, amortized resizing, and hash map collision resolution strategies.",
        "content_markdown": "# Arrays & Hashing\n\nArrays provide O(1) random access by memory indexing...",
        "estimated_read_time_minutes": 8,
        "difficulty_level": "Easy",
        "order_index": 1
    },
    {
        "slug": "graph-traversal-bfs-dfs",
        "title": "Graph Traversal: BFS & DFS Foundations",
        "category": "DSA",
        "summary": "Queue-based level-order search and recursive backtracking traversal across graphs.",
        "content_markdown": "# Graph Traversals\n\nBreadth-First Search (BFS) and Depth-First Search (DFS) form the bedrock...",
        "estimated_read_time_minutes": 12,
        "difficulty_level": "Medium",
        "order_index": 2
    },
    {
        "slug": "operating-systems-concurrency",
        "title": "OS: Concurrency, Semaphores & Mutexes",
        "category": "OS",
        "summary": "Process synchronization, critical section problems, and deadlock conditions.",
        "content_markdown": "# OS Concurrency\n\nSynchronization primitives prevent race conditions in multithreaded systems...",
        "estimated_read_time_minutes": 15,
        "difficulty_level": "Hard",
        "order_index": 3
    },
    {
        "slug": "dbms-indexing-b-trees",
        "title": "DBMS: B+ Tree Indexing & Query Plans",
        "category": "DBMS",
        "summary": "Disk-based data structures, balanced search trees, and execution plan cost estimation.",
        "content_markdown": "# Database Indexing\n\nB+ trees minimize disk I/O operations by maintaining a high fanout...",
        "estimated_read_time_minutes": 14,
        "difficulty_level": "Medium",
        "order_index": 4
    }
]

async def _ensure_seeded(db: AsyncSession):
    count_res = await db.execute(select(LearningModule))
    if not count_res.scalars().first():
        for mod_data in DEFAULT_MODULES:
            db.add(LearningModule(**mod_data))
        await db.commit()

# --- CURRICULUM & MODULE ENDPOINTS (FEAT-123..FEAT-125, FEAT-134, FEAT-135) ---

@router.get("/learn/modules", response_model=LearningModuleListResponse)
async def list_learning_modules(
    category: Optional[str] = Query(None, description="Filter by category (DSA, OS, DBMS, CN, OOPS)"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty (Easy, Medium, Hard) - FEAT-135"),
    search: Optional[str] = Query(None, description="Fuzzy search across titles and summaries - FEAT-134"),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve curriculum learning modules with multi-parameter filtering (FEAT-123, FEAT-134, FEAT-135)."""
    await _ensure_seeded(db)

    query = select(LearningModule).where(LearningModule.is_published == True)
    if category and category.lower() != "all":
        query = query.where(LearningModule.category.ilike(category))
    if difficulty and difficulty.lower() != "all":
        query = query.where(LearningModule.difficulty_level.ilike(difficulty))
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            LearningModule.title.ilike(search_pattern) | 
            LearningModule.summary.ilike(search_pattern) |
            LearningModule.content_markdown.ilike(search_pattern)
        )
    query = query.order_by(LearningModule.order_index)

    exec_res = await db.execute(query)
    filtered = exec_res.scalars().all()
    return LearningModuleListResponse(modules=filtered, total=len(filtered))

@router.get("/learn/modules/{slug}", response_model=LearningModuleResponse)
async def get_learning_module(
    slug: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve an individual learning concept module by its URL slug (FEAT-123, FEAT-125)."""
    await _ensure_seeded(db)
    res = await db.execute(select(LearningModule).where(LearningModule.slug == slug))
    module = res.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=404, detail="Learning module not found.")
    return module

# --- FEAT-126: SOCRATIC AI CONCEPT TUTOR ---
@router.post("/learn/socratic-tutor", response_model=SocraticTutorResponse)
async def get_socratic_guidance(
    payload: SocraticTutorRequest,
    current_user: User = Depends(get_current_user)
):
    """Ask doubts on any concept and receive progressive Socratic guided explanations (FEAT-126)."""
    if not payload.student_query.strip():
        raise HTTPException(status_code=400, detail="Student query cannot be empty.")
    guidance = LearningService.get_socratic_guidance(payload.concept_slug, payload.student_query)
    return SocraticTutorResponse(**guidance)

# --- FEAT-127: INTERACTIVE CODE SNIPPET SANDBOX ---
@router.post("/learn/snippet-sandbox", response_model=CodeSnippetSimResponse)
async def run_snippet_sandbox(
    payload: CodeSnippetSimRequest,
    current_user: User = Depends(get_current_user)
):
    """Simulate code execution and AST syntax tree analysis safely inside articles (FEAT-127)."""
    result = LearningService.simulate_snippet_execution(payload.language, payload.code, payload.stdin)
    return CodeSnippetSimResponse(**result)

# --- FEAT-130: VIDEO & VISUAL RESOURCE CURATOR ---
@router.get("/learn/modules/{slug}/resources", response_model=List[VisualResource])
async def get_module_visual_resources(
    slug: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Curated high-quality free video lectures and animations for a topic (FEAT-130)."""
    return LearningService.get_curated_resources(slug)

# --- FEAT-131: PRACTICE PROBLEM LINKER ---
@router.get("/learn/modules/{slug}/problems", response_model=List[PracticeProblem])
async def get_module_practice_problems(
    slug: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Link relevant Coding Arena and assessment problems to topic (FEAT-131)."""
    return LearningService.get_practice_problems(slug)

# --- FEAT-132: DOWNLOADABLE CONCEPT CHEAT SHEETS ---
@router.get("/learn/modules/{slug}/cheat-sheet", response_model=CheatSheetResponse)
async def get_concept_cheat_sheet(
    slug: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Generate high-yield one-page summary cheat sheet for quick revision (FEAT-132)."""
    return LearningService.get_cheat_sheet(slug)

# --- FEAT-133: MULTILINGUAL LEARNING LANGUAGE SELECTOR ---
@router.get("/learn/modules/{slug}/translate", response_model=MultilingualContentResponse)
async def get_multilingual_module_content(
    slug: str,
    lang: str = Query("hi", description="Target language code: hi (Hindi), en (English)"),
    db: AsyncSession = Depends(get_db_session)
):
    """Read concept notes in Hindi and regional translations (FEAT-133)."""
    return LearningService.get_multilingual_content(slug, lang)

# --- FEAT-135: TOPIC DIFFICULTY RATING & FEEDBACK ---
@router.post("/learn/modules/{slug}/feedback", response_model=TopicFeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_topic_feedback(
    slug: str,
    payload: TopicFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Rate topic difficulty (1-5) and submit confusing section feedback (FEAT-135)."""
    await _ensure_seeded(db)
    mod_res = await db.execute(select(LearningModule).where(LearningModule.slug == slug))
    module = mod_res.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=404, detail="Learning module not found.")

    feedback = TopicFeedback(
        user_id=current_user.id,
        module_id=module.id,
        difficulty_rating=payload.difficulty_rating,
        confusing_sections=payload.confusing_sections,
        feedback_text=payload.feedback_text
    )
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    return feedback

# --- FEAT-137: REAL-WORLD ARCHITECTURE CASE STUDIES ---
@router.get("/learn/case-studies", response_model=List[ArchitectureCaseStudy])
async def get_architecture_case_studies():
    """Deep-dive case studies into real-world architectures (Netflix, Uber, WhatsApp) - FEAT-137."""
    return LearningService.get_architecture_case_studies()

# --- FEAT-138: INTERACTIVE FLASH QUIZ CHECKPOINTS ---
@router.get("/learn/modules/{slug}/quiz", response_model=FlashQuizResponse)
async def get_module_flash_quiz(
    slug: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Mini 2-minute checkpoints interspersed within reading material (FEAT-138)."""
    questions = LearningService.get_flash_quiz(slug)
    return FlashQuizResponse(slug=slug, questions=questions)

@router.post("/learn/modules/{slug}/quiz/submit", response_model=FlashQuizResultResponse)
async def submit_flash_quiz(
    slug: str,
    payload: FlashQuizSubmitRequest,
    current_user: User = Depends(get_current_user)
):
    """Grade flash quiz checkpoint and return instant scoring and explanations (FEAT-138)."""
    quiz_questions = LearningService.get_flash_quiz(slug)
    total = len(quiz_questions)
    score = 0
    review = []
    
    for q in quiz_questions:
        qid = q["id"]
        chosen = payload.answers.get(qid)
        correct = q["correct_option_index"]
        is_correct = (chosen == correct)
        if is_correct:
            score += 1
        review.append({
            "question_id": qid,
            "is_correct": is_correct,
            "chosen_index": chosen,
            "correct_index": correct,
            "explanation": q["explanation"]
        })

    percentage = round((score / total) * 100, 1) if total > 0 else 0
    passed = percentage >= 50.0
    return FlashQuizResultResponse(
        score=score,
        total_questions=total,
        percentage=percentage,
        passed=passed,
        review=review
    )

# --- FEAT-144: CURRICULUM VERSIONING & CHANGELOG ---
@router.get("/learn/changelog", response_model=List[CurriculumChangelogEntry])
async def get_curriculum_changelog():
    """Tracks updates to curriculum notes with historical revision diffs (FEAT-144)."""
    return LearningService.get_curriculum_changelog()

# --- STUDENT PROGRESS & MASTERY (FEAT-128, FEAT-129) ---

@router.post("/learn/modules/{slug}/progress", response_model=TopicProgressResponse)
async def record_topic_progress(
    slug: str,
    payload: TopicProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Record student topic reading completion and mastery score (FEAT-128, FEAT-129)."""
    await _ensure_seeded(db)
    mod_res = await db.execute(select(LearningModule).where(LearningModule.slug == slug))
    module = mod_res.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=404, detail="Learning module not found.")

    res = await db.execute(
        select(StudentTopicProgress).where(
            and_(
                StudentTopicProgress.user_id == current_user.id,
                StudentTopicProgress.module_id == module.id
            )
        )
    )
    progress = res.scalar_one_or_none()

    if not progress:
        progress = StudentTopicProgress(
            user_id=current_user.id,
            module_id=module.id,
            is_completed=payload.is_completed,
            mastery_score=payload.mastery_score
        )
        db.add(progress)
    else:
        progress.is_completed = payload.is_completed
        progress.mastery_score = payload.mastery_score

    await db.commit()
    await db.refresh(progress)
    return progress

@router.get("/learn/progress/me", response_model=List[TopicProgressResponse])
async def get_my_learning_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Fetch logged-in student's complete curriculum progress records (FEAT-128)."""
    res = await db.execute(select(StudentTopicProgress).where(StudentTopicProgress.user_id == current_user.id))
    return res.scalars().all()

# --- STUDENT NOTES & BOOKMARKS (FEAT-136, FEAT-139) ---

@router.post("/learn/modules/{slug}/notes", response_model=TopicNoteResponse, status_code=status.HTTP_201_CREATED)
async def create_topic_note(
    slug: str,
    payload: TopicNoteCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Create or bookmark personal study note anchored to a concept module (FEAT-136, FEAT-139)."""
    await _ensure_seeded(db)
    mod_res = await db.execute(select(LearningModule).where(LearningModule.slug == slug))
    module = mod_res.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=404, detail="Learning module not found.")

    note = StudentTopicNote(
        user_id=current_user.id,
        module_id=module.id,
        note_content=payload.note_content,
        is_bookmarked=payload.is_bookmarked
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note

@router.get("/learn/modules/{slug}/notes", response_model=List[TopicNoteResponse])
async def get_my_topic_notes(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Fetch personal study notes for a specific topic with strict IDOR ownership checks (FEAT-136)."""
    await _ensure_seeded(db)
    mod_res = await db.execute(select(LearningModule).where(LearningModule.slug == slug))
    module = mod_res.scalar_one_or_none()
    if not module:
        raise HTTPException(status_code=404, detail="Learning module not found.")

    res = await db.execute(
        select(StudentTopicNote).where(
            and_(
                StudentTopicNote.user_id == current_user.id,
                StudentTopicNote.module_id == module.id
            )
        )
    )
    return res.scalars().all()

# --- DSA VISUALIZATION SIMULATION ENGINE (FEAT-163..FEAT-180) ---

@router.post("/dsaviz/simulate/traversal", response_model=AlgorithmTraceResponse)
async def simulate_graph_traversal(
    payload: GraphTraversalRequest
):
    """Simulate BFS or DFS traversal on a custom or pre-built graph (FEAT-163, FEAT-164, FEAT-165, FEAT-172)."""
    algo = payload.algorithm.lower()
    if algo == "bfs":
        trace = AlgorithmTraceEngine.trace_bfs(payload.nodes, payload.edges, payload.start_node)
    elif algo == "dfs":
        trace = AlgorithmTraceEngine.trace_dfs(payload.nodes, payload.edges, payload.start_node)
    else:
        raise HTTPException(status_code=400, detail="Supported algorithms are 'bfs' and 'dfs'.")
    return trace

@router.post("/dsaviz/simulate/shortest-path", response_model=AlgorithmTraceResponse)
async def simulate_shortest_path(
    payload: ShortestPathRequest
):
    """Simulate Dijkstra shortest path computation (FEAT-179)."""
    algo = payload.algorithm.lower()
    if algo == "dijkstra":
        trace = AlgorithmTraceEngine.trace_dijkstra(payload.nodes, payload.edges, payload.start_node)
    else:
        raise HTTPException(status_code=400, detail="Supported algorithm is 'dijkstra'.")
    return trace

@router.get("/dsaviz/simulate/knapsack", response_model=AlgorithmTraceResponse)
async def simulate_knapsack_dp(
    capacity: int = Query(7, ge=1, le=50),
):
    """Simulate 0/1 Knapsack dynamic programming table calculation (FEAT-180)."""
    weights = [2, 3, 4, 5]
    values = [3, 4, 5, 6]
    return AlgorithmTraceEngine.trace_knapsack(weights, values, capacity)
