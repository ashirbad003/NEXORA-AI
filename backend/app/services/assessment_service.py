import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from backend.app.models.assessment import (
    AssessmentTest, AssessmentQuestion, AssessmentAttempt, AssessmentAnswer
)
from backend.app.schemas.assessment import (
    AssessmentTestCreateSchema, QuestionCreateSchema, AnswerBatchSaveSchema
)

class AssessmentService:
    @staticmethod
    async def list_published_tests(db: AsyncSession) -> List[Dict[str, Any]]:
        stmt = select(AssessmentTest).where(AssessmentTest.is_published == True).order_by(AssessmentTest.created_at.desc())
        result = await db.execute(stmt)
        tests = result.scalars().all()

        test_list = []
        for t in tests:
            # Count questions
            q_stmt = select(func.count(AssessmentQuestion.id)).where(AssessmentQuestion.test_id == t.id)
            q_res = await db.execute(q_stmt)
            q_count = q_res.scalar() or 0

            test_list.append({
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "category": t.category,
                "difficulty": t.difficulty,
                "duration_minutes": t.duration_minutes,
                "total_marks": t.total_marks,
                "pass_marks": t.pass_marks,
                "negative_marking_rate": t.negative_marking_rate,
                "retake_allowed": t.retake_allowed,
                "retake_cooldown_hours": t.retake_cooldown_hours,
                "company_template": t.company_template,
                "question_count": q_count
            })
        return test_list

    @staticmethod
    async def create_test(db: AsyncSession, data: AssessmentTestCreateSchema) -> AssessmentTest:
        test = AssessmentTest(
            title=data.title,
            description=data.description,
            category=data.category,
            difficulty=data.difficulty,
            duration_minutes=data.duration_minutes,
            total_marks=data.total_marks,
            pass_marks=data.pass_marks,
            negative_marking_rate=data.negative_marking_rate,
            retake_allowed=data.retake_allowed,
            retake_cooldown_hours=data.retake_cooldown_hours,
            company_template=data.company_template,
        )
        db.add(test)
        await db.flush()

        if data.questions:
            for idx, q_data in enumerate(data.questions):
                q = AssessmentQuestion(
                    test_id=test.id,
                    section_name=q_data.section_name,
                    order_index=q_data.order_index or idx,
                    question_text=q_data.question_text,
                    options=q_data.options,
                    correct_option=q_data.correct_option,
                    marks=q_data.marks,
                    explanation=q_data.explanation,
                    topic_tag=q_data.topic_tag,
                    difficulty=q_data.difficulty
                )
                db.add(q)
        await db.commit()
        await db.refresh(test)
        return test

    @staticmethod
    async def start_or_resume_attempt(db: AsyncSession, test_id: str, student_id: str) -> Dict[str, Any]:
        # 1. Fetch test
        test_stmt = select(AssessmentTest).where(AssessmentTest.id == test_id)
        test_res = await db.execute(test_stmt)
        test = test_res.scalar_one_or_none()
        if not test:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment test not found")

        # 2. Check for active in-progress attempt (FEAT-043: Interrupted Attempt Recovery)
        attempt_stmt = select(AssessmentAttempt).where(
            and_(
                AssessmentAttempt.test_id == test_id,
                AssessmentAttempt.student_id == student_id,
                AssessmentAttempt.status == "in_progress"
            )
        )
        attempt_res = await db.execute(attempt_stmt)
        attempt = attempt_res.scalar_one_or_none()

        now = datetime.utcnow()
        if attempt:
            # Check if expired on server (FEAT-041: Server-authoritative timing)
            deadline = attempt.start_time + timedelta(minutes=test.duration_minutes)
            if now >= deadline:
                attempt.status = "expired"
                attempt.end_time = deadline
                await db.commit()
                # If retake not allowed, reject
                if not test.retake_allowed:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assessment time has expired and retakes are disabled.")
                attempt = None

        if not attempt:
            # Check retake cooldown if previous attempt exists (FEAT-060)
            prev_stmt = select(AssessmentAttempt).where(
                and_(
                    AssessmentAttempt.test_id == test_id,
                    AssessmentAttempt.student_id == student_id,
                    AssessmentAttempt.status.in_(["completed", "expired"])
                )
            ).order_by(AssessmentAttempt.created_at.desc())
            prev_res = await db.execute(prev_stmt)
            prev_attempt = prev_res.scalars().first()
            if prev_attempt and not test.retake_allowed:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Retakes are not allowed for this assessment.")

            # Create new attempt
            attempt = AssessmentAttempt(
                test_id=test_id,
                student_id=student_id,
                status="in_progress",
                start_time=now,
                flagged_question_ids=[]
            )
            db.add(attempt)
            await db.flush()

        # Fetch questions
        q_stmt = select(AssessmentQuestion).where(AssessmentQuestion.test_id == test_id).order_by(AssessmentQuestion.order_index)
        q_res = await db.execute(q_stmt)
        questions = q_res.scalars().all()

        # FEAT-044: Question Randomization & Shuffling
        q_ids = [q.id for q in questions]
        if not attempt.shuffled_question_order:
            rng = random.Random(attempt.id)
            shuffled_ids = list(q_ids)
            rng.shuffle(shuffled_ids)
            attempt.shuffled_question_order = shuffled_ids
            await db.commit()
        else:
            shuffled_ids = attempt.shuffled_question_order

        # Order questions according to shuffled_ids
        q_map = {q.id: q for q in questions}
        ordered_questions = [q_map[qid] for qid in shuffled_ids if qid in q_map]

        # Calculate remaining seconds (server-authoritative)
        elapsed = (now - attempt.start_time).total_seconds()
        remaining = max(0, int(test.duration_minutes * 60 - elapsed))

        # Fetch saved answers (FEAT-042)
        ans_stmt = select(AssessmentAnswer).where(AssessmentAnswer.attempt_id == attempt.id)
        ans_res = await db.execute(ans_stmt)
        saved_answers = {ans.question_id: ans.selected_option for ans in ans_res.scalars().all() if ans.selected_option}

        formatted_questions = []
        for q in ordered_questions:
            formatted_questions.append({
                "id": q.id,
                "section_name": q.section_name,
                "order_index": q.order_index,
                "question_text": q.question_text,
                "options": q.options,
                "marks": q.marks,
                "topic_tag": q.topic_tag,
                "difficulty": q.difficulty
            })

        return {
            "attempt_id": attempt.id,
            "test_id": test.id,
            "duration_minutes": test.duration_minutes,
            "remaining_seconds": remaining,
            "shuffled_questions": formatted_questions,
            "saved_answers": saved_answers,
            "flagged_question_ids": attempt.flagged_question_ids or [],
            "blur_count": attempt.blur_count
        }

    @staticmethod
    async def save_answers_batch(
        db: AsyncSession, attempt_id: str, student_id: str, data: AnswerBatchSaveSchema
    ) -> Dict[str, Any]:
        attempt_stmt = select(AssessmentAttempt).where(
            and_(AssessmentAttempt.id == attempt_id, AssessmentAttempt.student_id == student_id)
        )
        attempt_res = await db.execute(attempt_stmt)
        attempt = attempt_res.scalar_one_or_none()
        if not attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment attempt not found")
        if attempt.status != "in_progress":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Attempt is no longer in progress")

        # Update blur count and flags
        if data.blur_count is not None and data.blur_count > attempt.blur_count:
            attempt.blur_count = data.blur_count  # FEAT-053
        if data.flagged_question_ids is not None:
            attempt.flagged_question_ids = data.flagged_question_ids  # FEAT-046

        # Upsert answers (FEAT-042: Auto-Save Answer State)
        now = datetime.utcnow()
        for item in data.answers:
            ans_stmt = select(AssessmentAnswer).where(
                and_(AssessmentAnswer.attempt_id == attempt_id, AssessmentAnswer.question_id == item.question_id)
            )
            ans_res = await db.execute(ans_stmt)
            ans = ans_res.scalar_one_or_none()
            if not ans:
                ans = AssessmentAnswer(
                    attempt_id=attempt_id,
                    question_id=item.question_id,
                    selected_option=item.selected_option,
                    time_spent_seconds=item.time_spent_seconds,
                    last_saved_at=now
                )
                db.add(ans)
            else:
                ans.selected_option = item.selected_option
                ans.time_spent_seconds = item.time_spent_seconds
                ans.last_saved_at = now

        await db.commit()
        return {"status": "saved", "saved_count": len(data.answers), "blur_count": attempt.blur_count}

    @staticmethod
    async def submit_attempt(db: AsyncSession, attempt_id: str, student_id: str) -> Dict[str, Any]:
        attempt_stmt = select(AssessmentAttempt).where(
            and_(AssessmentAttempt.id == attempt_id, AssessmentAttempt.student_id == student_id)
        )
        attempt_res = await db.execute(attempt_stmt)
        attempt = attempt_res.scalar_one_or_none()
        if not attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment attempt not found")
        if attempt.status == "completed":
            return await AssessmentService.get_scorecard(db, attempt_id, student_id)

        test_stmt = select(AssessmentTest).where(AssessmentTest.id == attempt.test_id)
        test_res = await db.execute(test_stmt)
        test = test_res.scalar_one_or_none()

        now = datetime.utcnow()
        attempt.status = "completed"
        attempt.end_time = now

        # Fetch questions and submitted answers
        q_stmt = select(AssessmentQuestion).where(AssessmentQuestion.test_id == test.id)
        q_res = await db.execute(q_stmt)
        questions = q_res.scalars().all()

        ans_stmt = select(AssessmentAnswer).where(AssessmentAnswer.attempt_id == attempt.id)
        ans_res = await db.execute(ans_stmt)
        answers_map = {ans.question_id: ans for ans in ans_res.scalars().all()}

        total_score = 0.0
        correct_count = 0
        incorrect_count = 0
        unattempted_count = 0
        weak_tags = set()

        # FEAT-045: Negative Marking Evaluator
        neg_rate = test.negative_marking_rate

        for q in questions:
            ans = answers_map.get(q.id)
            if not ans or not ans.selected_option:
                unattempted_count += 1
                if ans:
                    ans.is_correct = False
                    ans.marks_awarded = 0.0
            elif ans.selected_option.strip().upper() == q.correct_option.strip().upper():
                correct_count += 1
                ans.is_correct = True
                ans.marks_awarded = q.marks
                total_score += q.marks
            else:
                incorrect_count += 1
                ans.is_correct = False
                ans.marks_awarded = -neg_rate
                total_score -= neg_rate
                weak_tags.add(q.topic_tag)  # FEAT-055: Weak Area Tag Extractor

        attempt.score = max(0.0, round(total_score, 2))
        attempt.accuracy_percentage = round((correct_count / len(questions) * 100) if questions else 0.0, 1)

        # Percentile estimate against previous attempts
        all_attempts_stmt = select(AssessmentAttempt.score).where(AssessmentAttempt.test_id == test.id)
        all_attempts_res = await db.execute(all_attempts_stmt)
        all_scores = [s[0] for s in all_attempts_res.all()]
        if all_scores:
            below_count = sum(1 for s in all_scores if s <= attempt.score)
            attempt.percentile = round((below_count / len(all_scores)) * 100, 1)
        else:
            attempt.percentile = 100.0

        await db.commit()
        return await AssessmentService.get_scorecard(db, attempt_id, student_id)

    @staticmethod
    async def get_scorecard(db: AsyncSession, attempt_id: str, student_id: str) -> Dict[str, Any]:
        attempt_stmt = select(AssessmentAttempt).where(
            and_(AssessmentAttempt.id == attempt_id, AssessmentAttempt.student_id == student_id)
        )
        attempt_res = await db.execute(attempt_stmt)
        attempt = attempt_res.scalar_one_or_none()
        if not attempt:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assessment attempt not found")

        test_stmt = select(AssessmentTest).where(AssessmentTest.id == attempt.test_id)
        test_res = await db.execute(test_stmt)
        test = test_res.scalar_one_or_none()

        q_stmt = select(AssessmentQuestion).where(AssessmentQuestion.test_id == test.id).order_by(AssessmentQuestion.order_index)
        q_res = await db.execute(q_stmt)
        questions = q_res.scalars().all()

        ans_stmt = select(AssessmentAnswer).where(AssessmentAnswer.attempt_id == attempt.id)
        ans_res = await db.execute(ans_stmt)
        answers_map = {ans.question_id: ans for ans in ans_res.scalars().all()}

        time_taken = int((attempt.end_time - attempt.start_time).total_seconds()) if attempt.end_time else 0
        correct_count = 0
        incorrect_count = 0
        unattempted_count = 0
        weak_tags = set()
        section_stats: Dict[str, Dict[str, Any]] = {}
        solutions = []

        for q in questions:
            sec = q.section_name or "General"
            if sec not in section_stats:
                section_stats[sec] = {"total": 0, "correct": 0, "score": 0.0}
            section_stats[sec]["total"] += 1

            ans = answers_map.get(q.id)
            selected = ans.selected_option if ans else None
            is_correct = ans.is_correct if ans else False

            if not selected:
                unattempted_count += 1
            elif is_correct:
                correct_count += 1
                section_stats[sec]["correct"] += 1
                section_stats[sec]["score"] += q.marks
            else:
                incorrect_count += 1
                section_stats[sec]["score"] -= test.negative_marking_rate
                weak_tags.add(q.topic_tag)

            # FEAT-049: Detailed Solution & Explanation Viewer
            solutions.append({
                "question_id": q.id,
                "question_text": q.question_text,
                "options": q.options,
                "selected_option": selected,
                "correct_option": q.correct_option,
                "is_correct": is_correct,
                "explanation": q.explanation or f"Correct answer is {q.correct_option}.",
                "topic_tag": q.topic_tag,
                "section_name": q.section_name
            })

        return {
            "attempt_id": attempt.id,
            "test_title": test.title,
            "status": attempt.status,
            "score": attempt.score,
            "total_marks": test.total_marks,
            "accuracy_percentage": attempt.accuracy_percentage,
            "percentile": attempt.percentile,
            "time_taken_seconds": time_taken,
            "total_questions": len(questions),
            "correct_count": correct_count,
            "incorrect_count": incorrect_count,
            "unattempted_count": unattempted_count,
            "section_breakdown": section_stats,
            "weak_topic_tags": list(weak_tags),  # FEAT-055
            "solution_keys": solutions
        }

    @staticmethod
    async def get_historical_trends(db: AsyncSession, student_id: str) -> List[Dict[str, Any]]:
        # FEAT-054: Historical Assessment Trends
        stmt = select(AssessmentAttempt, AssessmentTest).join(
            AssessmentTest, AssessmentAttempt.test_id == AssessmentTest.id
        ).where(
            and_(AssessmentAttempt.student_id == student_id, AssessmentAttempt.status == "completed")
        ).order_by(AssessmentAttempt.created_at.asc())
        res = await db.execute(stmt)
        rows = res.all()

        history = []
        for attempt, test in rows:
            history.append({
                "attempt_id": attempt.id,
                "test_title": test.title,
                "category": test.category,
                "score": attempt.score,
                "accuracy": attempt.accuracy_percentage,
                "percentile": attempt.percentile,
                "date": attempt.created_at.strftime("%Y-%m-%d")
            })
        return history

    @staticmethod
    async def get_public_leaderboard(db: AsyncSession, test_id: str) -> List[Dict[str, Any]]:
        # FEAT-056: Leaderboard for Public Assessments
        from backend.app.models.auth import User
        stmt = select(AssessmentAttempt, User.email).join(
            User, AssessmentAttempt.student_id == User.id
        ).where(
            and_(AssessmentAttempt.test_id == test_id, AssessmentAttempt.status == "completed")
        ).order_by(AssessmentAttempt.score.desc(), AssessmentAttempt.accuracy_percentage.desc()).limit(20)
        res = await db.execute(stmt)
        rows = res.all()

        ranks = []
        for rank, (attempt, email) in enumerate(rows, start=1):
            masked_email = email.split("@")[0][:3] + "***@" + email.split("@")[1]
            ranks.append({
                "rank": rank,
                "student": masked_email,
                "score": attempt.score,
                "accuracy": attempt.accuracy_percentage,
                "percentile": attempt.percentile
            })
        return ranks
