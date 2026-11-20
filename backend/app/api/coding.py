from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from typing import List, Optional

from backend.app.db.session import get_db_session
from backend.app.api.deps import get_current_user, require_roles
from backend.app.models.auth import User
from backend.app.models.coding import (
    CodingProblem, ProblemTestCase, CodeSubmission, StudentCodingStats
)
from backend.app.schemas.user import UserRoleEnum
from backend.app.schemas.coding import (
    CodingProblemListItem, CodingProblemDetailResponse, CodingProblemListResponse,
    TestCaseSampleResponse, CodeRunRequest, CodeRunResponse,
    CodeSubmitRequest, SubmissionResultResponse, StudentCodingStatsResponse
)
from backend.app.services.coding_service import CodingArenaService
from sandbox.worker import ProcessIsolatedSandbox

router = APIRouter(prefix="/coding", tags=["Coding Arena & Sandbox"])

sandbox = ProcessIsolatedSandbox(timeout_seconds=3)

# --- PROBLEM BROWSING & CATALOG (FEAT-065, FEAT-066, FEAT-079, FEAT-080) ---

@router.get("/problems", response_model=CodingProblemListResponse)
async def list_coding_problems(
    difficulty: Optional[str] = Query(None, description="Easy, Medium, Hard"),
    category: Optional[str] = Query(None, description="Arrays, Stacks, DP, etc."),
    company: Optional[str] = Query(None, description="Google, Amazon, Meta, etc. (FEAT-066)"),
    search: Optional[str] = Query(None, description="Fuzzy search across problem titles and tags"),
    db: AsyncSession = Depends(get_db_session)
):
    """Browse coding problems with multi-dimensional filtering (FEAT-065, FEAT-066)."""
    await CodingArenaService.ensure_problems_seeded(db)

    query = select(CodingProblem).where(CodingProblem.is_published == True)
    if difficulty and difficulty.lower() != "all":
        query = query.where(CodingProblem.difficulty.ilike(difficulty))
    if category and category.lower() != "all":
        query = query.where(CodingProblem.category.ilike(category))
    if company and company.lower() != "all":
        query = query.where(CodingProblem.companies.ilike(f"%{company}%"))
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            CodingProblem.title.ilike(search_pattern) | 
            CodingProblem.tags.ilike(search_pattern)
        )

    res = await db.execute(query)
    problems = res.scalars().all()
    return CodingProblemListResponse(problems=problems, total=len(problems))

@router.get("/problems/{slug}", response_model=CodingProblemDetailResponse)
async def get_coding_problem_detail(
    slug: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve problem details and public sample test cases (FEAT-065, FEAT-067). Shields hidden test cases."""
    await CodingArenaService.ensure_problems_seeded(db)

    res = await db.execute(select(CodingProblem).where(CodingProblem.slug == slug))
    problem = res.scalar_one_or_none()
    if not problem:
        raise HTTPException(status_code=404, detail="Coding problem not found.")

    # Fetch ONLY sample test cases (FEAT-067) - Hidden cases (FEAT-068) are never returned publicly
    tc_res = await db.execute(
        select(ProblemTestCase).where(
            and_(
                ProblemTestCase.problem_id == problem.id,
                ProblemTestCase.is_sample == True
            )
        ).order_by(ProblemTestCase.order_index)
    )
    samples = tc_res.scalars().all()

    return CodingProblemDetailResponse(
        id=problem.id,
        slug=problem.slug,
        title=problem.title,
        difficulty=problem.difficulty,
        category=problem.category,
        tags=problem.tags,
        companies=problem.companies,
        description_markdown=problem.description_markdown,
        constraints=problem.constraints,
        time_limit_ms=problem.time_limit_ms,
        memory_limit_mb=problem.memory_limit_mb,
        starter_code_python=problem.starter_code_python,
        starter_code_java=problem.starter_code_java,
        starter_code_cpp=problem.starter_code_cpp,
        starter_code_c=problem.starter_code_c,
        sample_test_cases=samples,
        created_at=problem.created_at
    )

# --- RUN CODE (CUSTOM INPUT / SAMPLE EXECUTION - FEAT-067, FEAT-077) ---

@router.post("/problems/{slug}/run", response_model=CodeRunResponse)
async def run_custom_code(
    slug: str,
    payload: CodeRunRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Run code against sample test case or custom input in isolated sandbox (FEAT-067, FEAT-077)."""
    await CodingArenaService.ensure_problems_seeded(db)

    res = await db.execute(select(CodingProblem).where(CodingProblem.slug == slug))
    problem = res.scalar_one_or_none()
    if not problem:
        raise HTTPException(status_code=404, detail="Coding problem not found.")

    exec_result = sandbox.execute(payload.language, payload.code, payload.custom_input or "")

    return CodeRunResponse(
        language=payload.language,
        status=exec_result["status"],
        stdout=exec_result["stdout"],
        stderr=exec_result["stderr"],
        execution_time_ms=exec_result["execution_time_ms"],
        memory_used_mb=exec_result["memory_used_mb"],
        is_timeout=exec_result["is_timeout"],
        isolation_boundary=exec_result["isolation_boundary"]
    )

# --- SUBMIT SOLUTION (OFFICIAL EVALUATION - FEAT-068, FEAT-073) ---

@router.post("/problems/{slug}/submit", response_model=SubmissionResultResponse, status_code=status.HTTP_201_CREATED)
async def submit_solution(
    slug: str,
    payload: CodeSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Submit code solution for official evaluation against sample and hidden test cases (FEAT-068, FEAT-073)."""
    await CodingArenaService.ensure_problems_seeded(db)

    res = await db.execute(select(CodingProblem).where(CodingProblem.slug == slug))
    problem = res.scalar_one_or_none()
    if not problem:
        raise HTTPException(status_code=404, detail="Coding problem not found.")

    # Fetch ALL test cases (sample + hidden) securely on backend
    tc_res = await db.execute(
        select(ProblemTestCase).where(ProblemTestCase.problem_id == problem.id).order_by(ProblemTestCase.order_index)
    )
    all_test_cases = tc_res.scalars().all()

    # Evaluate submission via isolated sandbox
    eval_result = await CodingArenaService.evaluate_submission(
        problem=problem,
        language=payload.language,
        code=payload.code,
        test_cases=all_test_cases,
        sandbox=sandbox
    )

    # Persist submission record in PostgreSQL
    submission = CodeSubmission(
        user_id=current_user.id,
        problem_id=problem.id,
        language=payload.language,
        code_content=payload.code,
        verdict=eval_result["verdict"],
        passed_test_cases=eval_result["passed_cases"],
        total_test_cases=eval_result["total_cases"],
        execution_time_ms=eval_result["execution_time_ms"],
        memory_used_mb=eval_result["memory_used_mb"],
        error_message=eval_result["error_message"]
    )
    db.add(submission)

    # Update student coding statistics (FEAT-074)
    if eval_result["verdict"] == "ACCEPTED":
        stats_res = await db.execute(
            select(StudentCodingStats).where(StudentCodingStats.user_id == current_user.id)
        )
        stats = stats_res.scalar_one_or_none()
        if not stats:
            stats = StudentCodingStats(
                user_id=current_user.id,
                total_solved=1,
                easy_solved=1 if problem.difficulty == "Easy" else 0,
                medium_solved=1 if problem.difficulty == "Medium" else 0,
                hard_solved=1 if problem.difficulty == "Hard" else 0,
                current_streak_days=1,
                longest_streak_days=1
            )
            db.add(stats)
        else:
            stats.total_solved += 1
            if problem.difficulty == "Easy":
                stats.easy_solved += 1
            elif problem.difficulty == "Medium":
                stats.medium_solved += 1
            elif problem.difficulty == "Hard":
                stats.hard_solved += 1

    await db.commit()
    await db.refresh(submission)

    return SubmissionResultResponse(
        id=submission.id,
        problem_id=problem.id,
        problem_slug=problem.slug,
        problem_title=problem.title,
        language=submission.language,
        verdict=submission.verdict,
        passed_test_cases=submission.passed_test_cases,
        total_test_cases=submission.total_test_cases,
        execution_time_ms=submission.execution_time_ms,
        memory_used_mb=submission.memory_used_mb,
        error_message=submission.error_message,
        created_at=submission.created_at
    )

# --- SUBMISSION HISTORY & CODING STATS (FEAT-073, FEAT-074) ---

@router.get("/submissions/me", response_model=List[SubmissionResultResponse])
async def get_my_submissions(
    problem_slug: Optional[str] = Query(None, description="Filter submissions by problem"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve logged-in student's submission history with IDOR protection (FEAT-073)."""
    query = select(CodeSubmission).where(CodeSubmission.user_id == current_user.id)
    if problem_slug:
        p_res = await db.execute(select(CodingProblem).where(CodingProblem.slug == problem_slug))
        problem = p_res.scalar_one_or_none()
        if problem:
            query = query.where(CodeSubmission.problem_id == problem.id)

    query = query.order_by(desc(CodeSubmission.created_at))
    res = await db.execute(query)
    submissions = res.scalars().all()

    # Join problem metadata
    out = []
    for s in submissions:
        p_res = await db.execute(select(CodingProblem).where(CodingProblem.id == s.problem_id))
        prob = p_res.scalar_one_or_none()
        out.append(SubmissionResultResponse(
            id=s.id,
            problem_id=s.problem_id,
            problem_slug=prob.slug if prob else "unknown",
            problem_title=prob.title if prob else "Unknown Problem",
            language=s.language,
            verdict=s.verdict,
            passed_test_cases=s.passed_test_cases,
            total_test_cases=s.total_test_cases,
            execution_time_ms=s.execution_time_ms,
            memory_used_mb=s.memory_used_mb,
            error_message=s.error_message,
            created_at=s.created_at
        ))
    return out

@router.get("/stats/me", response_model=StudentCodingStatsResponse)
async def get_my_coding_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Retrieve student's coding activity stats and streak metrics (FEAT-074)."""
    res = await db.execute(
        select(StudentCodingStats).where(StudentCodingStats.user_id == current_user.id)
    )
    stats = res.scalar_one_or_none()
    if not stats:
        return StudentCodingStatsResponse(
            user_id=current_user.id,
            total_solved=0,
            easy_solved=0,
            medium_solved=0,
            hard_solved=0,
            current_streak_days=0,
            longest_streak_days=0
        )
    return stats
