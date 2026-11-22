from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db_session
from backend.app.api.deps import get_current_user
from backend.app.models.auth import User
from backend.app.schemas.phase10_peer import (
    ThreadCreate, ThreadResponse,
    ReplyCreate, ReplyResponse,
    StudyGroupCreate, StudyGroupResponse,
    PeerLeaderboardEntry
)
from backend.app.services.peer_service import PeerService

router = APIRouter(prefix="/community", tags=["Peer Learning & Community"])

# --- Threads ---

@router.post("/threads", response_model=ThreadResponse, status_code=status.HTTP_201_CREATED)
async def create_thread(
    payload: ThreadCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    thread = await PeerService.create_thread(db, current_user.id, payload)
    return ThreadResponse(
        id=thread.id,
        user_id=thread.user_id,
        author_name=current_user.full_name,
        title=thread.title,
        content=thread.content,
        category=thread.category,
        context_type=thread.context_type,
        context_id=thread.context_id,
        upvotes=thread.upvotes,
        reply_count=thread.reply_count,
        is_resolved=thread.is_resolved,
        status=thread.status,
        created_at=thread.created_at,
        updated_at=thread.updated_at
    )

@router.get("/threads", response_model=List[ThreadResponse])
async def list_threads(
    category: Optional[str] = None,
    context_id: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    return await PeerService.list_threads(db, category=category, context_id=context_id, search=search)

@router.get("/threads/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    return await PeerService.get_thread(db, thread_id)

@router.post("/threads/{thread_id}/upvote")
async def upvote_thread(
    thread_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    upvotes = await PeerService.upvote_thread(db, current_user.id, thread_id)
    return {"thread_id": thread_id, "upvotes": upvotes}

# --- Replies ---

@router.post("/threads/{thread_id}/replies", response_model=ReplyResponse, status_code=status.HTTP_201_CREATED)
async def add_reply(
    thread_id: str,
    payload: ReplyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    reply = await PeerService.add_reply(db, current_user.id, thread_id, payload)
    return ReplyResponse(
        id=reply.id,
        thread_id=reply.thread_id,
        user_id=reply.user_id,
        author_name=current_user.full_name,
        content=reply.content,
        code_snippet=reply.code_snippet,
        upvotes=reply.upvotes,
        is_accepted=reply.is_accepted,
        status=reply.status,
        created_at=reply.created_at
    )

@router.get("/threads/{thread_id}/replies", response_model=List[ReplyResponse])
async def list_replies(
    thread_id: str,
    db: AsyncSession = Depends(get_db_session)
):
    return await PeerService.list_replies(db, thread_id)

@router.post("/threads/{thread_id}/replies/{reply_id}/accept")
async def accept_reply(
    thread_id: str,
    reply_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    success = await PeerService.mark_reply_accepted(db, current_user.id, thread_id, reply_id)
    return {"success": success}

# --- Study Groups ---

@router.post("/groups", response_model=StudyGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_study_group(
    payload: StudyGroupCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    g = await PeerService.create_study_group(db, current_user.id, payload)
    return StudyGroupResponse(
        id=g.id,
        creator_id=g.creator_id,
        name=g.name,
        description=g.description,
        goal_description=g.goal_description,
        is_private=g.is_private,
        invite_code=g.invite_code,
        member_count=g.member_count,
        is_member=True,
        created_at=g.created_at
    )

@router.get("/groups", response_model=List[StudyGroupResponse])
async def list_study_groups(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    return await PeerService.list_study_groups(db, current_user.id)

@router.post("/groups/{group_id}/join")
async def join_study_group(
    group_id: str,
    invite_code: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    success = await PeerService.join_study_group(db, current_user.id, group_id, invite_code)
    return {"joined": success}

# --- Leaderboard ---

@router.get("/leaderboard", response_model=List[PeerLeaderboardEntry])
async def get_peer_leaderboard(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session)
):
    return await PeerService.get_leaderboard(db, limit)
