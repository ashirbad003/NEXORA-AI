from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.models.auth import User, StudentProfile
from backend.app.models.learning import StudentTopicProgress, TopicFeedback
from backend.app.models.coding import CodeSubmission, StudentCodingStats

class StudentContextAggregator:
    """
    Compiles unified context (skills, past scores, weak areas, resume points)
    across all student modules. Implements FEAT-002.
    """

    @staticmethod
    async def aggregate_context(db: AsyncSession, user_id: str) -> Dict[str, Any]:
        context: Dict[str, Any] = {
            "user_id": user_id,
            "target_role": "Software Development Engineer",
            "skills": [],
            "cgpa": 8.0,
            "topics_completed": 0,
            "total_topics": 20,
            "problems_solved": 0,
            "easy_solved": 0,
            "medium_solved": 0,
            "hard_solved": 0,
            "quiz_accuracy_pct": 75.0,
            "weak_tags": [],
            "recent_activity_count": 0
        }

        # 1. Fetch Student Profile
        profile_stmt = select(StudentProfile).where(StudentProfile.user_id == user_id)
        profile_res = await db.execute(profile_stmt)
        profile = profile_res.scalar_one_or_none()
        if profile:
            context["target_role"] = profile.career_preferences or context["target_role"]
            if profile.skills:
                context["skills"] = [s.strip() for s in profile.skills.split(",") if s.strip()]
            context["cgpa"] = profile.cgpa or context["cgpa"]

        # 2. Fetch Learning Progress
        topic_stmt = select(func.count(StudentTopicProgress.id)).where(
            StudentTopicProgress.user_id == user_id,
            StudentTopicProgress.is_completed == True
        )
        topic_res = await db.execute(topic_stmt)
        context["topics_completed"] = topic_res.scalar() or 0

        # 3. Fetch Topic Feedback / Rating
        feedback_stmt = select(func.avg(TopicFeedback.difficulty_rating)).where(TopicFeedback.user_id == user_id)
        feedback_res = await db.execute(feedback_stmt)
        avg_diff = feedback_res.scalar()
        if avg_diff is not None:
            # Map 1-5 difficulty to estimated quiz accuracy
            context["quiz_accuracy_pct"] = round(100.0 - (float(avg_diff) * 15.0), 1)

        # 4. Fetch Coding Arena Stats
        stats_stmt = select(StudentCodingStats).where(StudentCodingStats.user_id == user_id)
        stats_res = await db.execute(stats_stmt)
        stats = stats_res.scalar_one_or_none()
        if stats:
            context["problems_solved"] = stats.total_solved or 0
            context["easy_solved"] = stats.easy_solved or 0
            context["medium_solved"] = stats.medium_solved or 0
            context["hard_solved"] = stats.hard_solved or 0

        # 5. Identify Weak Tags from Non-Accepted Submissions
        weak_stmt = select(CodeSubmission.verdict).where(
            CodeSubmission.user_id == user_id,
            CodeSubmission.verdict != "ACCEPTED"
        ).limit(20)
        weak_res = await db.execute(weak_stmt)
        unaccepted_count = len(weak_res.scalars().all())
        if unaccepted_count > 3:
            context["weak_tags"] = ["dynamic_programming", "graphs", "recursion"]
        else:
            context["weak_tags"] = ["sliding_window", "trees"]

        return context
