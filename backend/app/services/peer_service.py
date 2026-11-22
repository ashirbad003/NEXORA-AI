import re
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, text, and_, or_, desc
from fastapi import HTTPException, status

from backend.app.models.phase10_peer import (
    PeerDiscussionThread, PeerDiscussionReply, PeerStudyGroup, PeerStudyGroupMember
)
from backend.app.models.auth import User
from backend.app.schemas.phase10_peer import (
    ThreadCreate, ReplyCreate, StudyGroupCreate
)

TOXIC_KEYWORDS = {
    "abuse", "harass", "threat", "violence", "hate", "scam", "cheat", "plagiarize", "idiot", "moron"
}

class PeerService:

    @staticmethod
    def _is_toxic_content(text: str) -> bool:
        lower = text.lower()
        for word in TOXIC_KEYWORDS:
            if re.search(r'\b' + re.escape(word) + r'\b', lower):
                return True
        return False

    # --- Threads ---

    @classmethod
    async def create_thread(cls, db: AsyncSession, user_id: str, data: ThreadCreate) -> PeerDiscussionThread:
        status_flag = "FLAGGED" if (cls._is_toxic_content(data.title) or cls._is_toxic_content(data.content)) else "OPEN"
        thread = PeerDiscussionThread(
            user_id=user_id,
            title=data.title,
            content=data.content,
            category=data.category,
            context_type=data.context_type,
            context_id=data.context_id,
            upvotes=0,
            reply_count=0,
            is_resolved=False,
            status=status_flag
        )
        db.add(thread)
        await db.commit()
        await db.refresh(thread)
        return thread

    @classmethod
    async def list_threads(cls, db: AsyncSession, category: Optional[str] = None, context_id: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
        query = select(PeerDiscussionThread, User.full_name).join(
            User, PeerDiscussionThread.user_id == User.id
        ).where(PeerDiscussionThread.status != "FLAGGED")

        if category:
            query = query.where(PeerDiscussionThread.category == category)
        if context_id:
            query = query.where(PeerDiscussionThread.context_id == context_id)
        if search:
            query = query.where(PeerDiscussionThread.title.ilike(f"%{search}%"))

        query = query.order_by(desc(PeerDiscussionThread.created_at))
        results = (await db.execute(query)).all()

        threads = []
        for thread, author_name in results:
            threads.append({
                "id": thread.id,
                "user_id": thread.user_id,
                "author_name": author_name,
                "title": thread.title,
                "content": thread.content,
                "category": thread.category,
                "context_type": thread.context_type,
                "context_id": thread.context_id,
                "upvotes": thread.upvotes,
                "reply_count": thread.reply_count,
                "is_resolved": thread.is_resolved,
                "status": thread.status,
                "created_at": thread.created_at,
                "updated_at": thread.updated_at
            })
        return threads

    @classmethod
    async def get_thread(cls, db: AsyncSession, thread_id: str) -> Dict[str, Any]:
        query = select(PeerDiscussionThread, User.full_name).join(
            User, PeerDiscussionThread.user_id == User.id
        ).where(PeerDiscussionThread.id == thread_id)
        res = (await db.execute(query)).first()
        if not res:
            raise HTTPException(status_code=404, detail="Discussion thread not found")
        thread, author_name = res
        return {
            "id": thread.id,
            "user_id": thread.user_id,
            "author_name": author_name,
            "title": thread.title,
            "content": thread.content,
            "category": thread.category,
            "context_type": thread.context_type,
            "context_id": thread.context_id,
            "upvotes": thread.upvotes,
            "reply_count": thread.reply_count,
            "is_resolved": thread.is_resolved,
            "status": thread.status,
            "created_at": thread.created_at,
            "updated_at": thread.updated_at
        }

    @classmethod
    async def upvote_thread(cls, db: AsyncSession, user_id: str, thread_id: str) -> int:
        """
        FEAT-280: Upvoting engine with thread author self-upvote prevention.
        """
        thread = (await db.execute(select(PeerDiscussionThread).where(PeerDiscussionThread.id == thread_id))).scalar_one_or_none()
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        if thread.user_id == user_id:
            raise HTTPException(status_code=400, detail="Authors cannot upvote their own discussion thread.")

        thread.upvotes += 1
        await db.commit()
        return thread.upvotes

    # --- Replies ---

    @classmethod
    async def add_reply(cls, db: AsyncSession, user_id: str, thread_id: str, data: ReplyCreate) -> PeerDiscussionReply:
        thread = (await db.execute(select(PeerDiscussionThread).where(PeerDiscussionThread.id == thread_id))).scalar_one_or_none()
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")

        status_flag = "FLAGGED" if cls._is_toxic_content(data.content) else "ACTIVE"
        reply = PeerDiscussionReply(
            thread_id=thread_id,
            user_id=user_id,
            content=data.content,
            code_snippet=data.code_snippet,
            upvotes=0,
            is_accepted=False,
            status=status_flag
        )
        db.add(reply)
        thread.reply_count += 1
        await db.commit()
        await db.refresh(reply)
        return reply

    @classmethod
    async def list_replies(cls, db: AsyncSession, thread_id: str) -> List[Dict[str, Any]]:
        query = select(PeerDiscussionReply, User.full_name).join(
            User, PeerDiscussionReply.user_id == User.id
        ).where(
            PeerDiscussionReply.thread_id == thread_id,
            PeerDiscussionReply.status != "FLAGGED"
        ).order_by(
            desc(PeerDiscussionReply.is_accepted),
            desc(PeerDiscussionReply.upvotes),
            PeerDiscussionReply.created_at
        )
        results = (await db.execute(query)).all()
        replies = []
        for r, name in results:
            replies.append({
                "id": r.id,
                "thread_id": r.thread_id,
                "user_id": r.user_id,
                "author_name": name,
                "content": r.content,
                "code_snippet": r.code_snippet,
                "upvotes": r.upvotes,
                "is_accepted": r.is_accepted,
                "status": r.status,
                "created_at": r.created_at
            })
        return replies

    @classmethod
    async def mark_reply_accepted(cls, db: AsyncSession, user_id: str, thread_id: str, reply_id: str) -> bool:
        thread = (await db.execute(select(PeerDiscussionThread).where(PeerDiscussionThread.id == thread_id))).scalar_one_or_none()
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        if thread.user_id != user_id:
            raise HTTPException(status_code=403, detail="Only thread author can accept answers")

        reply = (await db.execute(select(PeerDiscussionReply).where(PeerDiscussionReply.id == reply_id, PeerDiscussionReply.thread_id == thread_id))).scalar_one_or_none()
        if not reply:
            raise HTTPException(status_code=404, detail="Reply not found")

        reply.is_accepted = True
        thread.is_resolved = True
        await db.commit()
        return True

    # --- Study Groups & Circles ---

    @classmethod
    async def create_study_group(cls, db: AsyncSession, user_id: str, data: StudyGroupCreate) -> PeerStudyGroup:
        invite_code = str(uuid.uuid4())[:8].upper()
        group = PeerStudyGroup(
            creator_id=user_id,
            name=data.name,
            description=data.description,
            goal_description=data.goal_description,
            is_private=data.is_private,
            invite_code=invite_code,
            member_count=1
        )
        db.add(group)
        await db.flush()

        member = PeerStudyGroupMember(
            group_id=group.id,
            user_id=user_id,
            role="ADMIN"
        )
        db.add(member)
        await db.commit()
        await db.refresh(group)
        return group

    @classmethod
    async def list_study_groups(cls, db: AsyncSession, user_id: str) -> List[Dict[str, Any]]:
        query = select(PeerStudyGroup).order_by(desc(PeerStudyGroup.created_at))
        groups = (await db.execute(query)).scalars().all()

        memberships = (await db.execute(
            select(PeerStudyGroupMember.group_id).where(PeerStudyGroupMember.user_id == user_id)
        )).scalars().all()
        membership_set = set(memberships)

        res = []
        for g in groups:
            res.append({
                "id": g.id,
                "creator_id": g.creator_id,
                "name": g.name,
                "description": g.description,
                "goal_description": g.goal_description,
                "is_private": g.is_private,
                "invite_code": g.invite_code if (g.creator_id == user_id or g.id in membership_set) else None,
                "member_count": g.member_count,
                "is_member": g.id in membership_set,
                "created_at": g.created_at
            })
        return res

    @classmethod
    async def join_study_group(cls, db: AsyncSession, user_id: str, group_id: str, invite_code: Optional[str] = None) -> bool:
        group = (await db.execute(select(PeerStudyGroup).where(PeerStudyGroup.id == group_id))).scalar_one_or_none()
        if not group:
            raise HTTPException(status_code=404, detail="Study group not found")

        if group.is_private and group.invite_code != invite_code:
            raise HTTPException(status_code=403, detail="Invalid invite code for private study group")

        existing = (await db.execute(
            select(PeerStudyGroupMember).where(
                PeerStudyGroupMember.group_id == group_id,
                PeerStudyGroupMember.user_id == user_id
            )
        )).scalar_one_or_none()
        if existing:
            return True  # Already joined

        member = PeerStudyGroupMember(
            group_id=group_id,
            user_id=user_id,
            role="MEMBER"
        )
        db.add(member)
        group.member_count += 1
        await db.commit()
        return True

    # --- Leaderboard & Karma ---

    @classmethod
    async def get_leaderboard(cls, db: AsyncSession, limit: int = 20) -> List[Dict[str, Any]]:
        stmt = text("""
            SELECT 
                u.id as user_id,
                u.full_name,
                COALESCE(rep.accepted_cnt, 0) as accepted_answers,
                COALESCE(th.thread_cnt, 0) as threads_started,
                (COALESCE(rep.accepted_cnt, 0) * 25 + COALESCE(rep.upvote_cnt, 0) * 5 + COALESCE(th.upvote_cnt, 0) * 2) as karma_points
            FROM users u
            LEFT JOIN (
                SELECT user_id, 
                       SUM(CASE WHEN is_accepted = TRUE THEN 1 ELSE 0 END) as accepted_cnt,
                       SUM(upvotes) as upvote_cnt
                FROM peer_discussion_replies
                WHERE status != 'FLAGGED'
                GROUP BY user_id
            ) rep ON rep.user_id = u.id
            LEFT JOIN (
                SELECT user_id, 
                       COUNT(*) as thread_cnt,
                       SUM(upvotes) as upvote_cnt
                FROM peer_discussion_threads
                WHERE status != 'FLAGGED'
                GROUP BY user_id
            ) th ON th.user_id = u.id
            WHERE (COALESCE(rep.accepted_cnt, 0) + COALESCE(th.thread_cnt, 0)) > 0
            ORDER BY karma_points DESC
            LIMIT :limit
        """)
        rows = (await db.execute(stmt, {"limit": limit})).fetchall()
        return [
            {
                "user_id": r.user_id,
                "full_name": r.full_name,
                "karma_points": r.karma_points,
                "accepted_answers": r.accepted_answers,
                "threads_started": r.threads_started
            }
            for r in rows
        ]
