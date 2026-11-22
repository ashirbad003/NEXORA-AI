from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db.session import get_db_session
from backend.app.api.deps import get_current_user, require_roles
from backend.app.models.auth import User
from backend.app.schemas.user import UserRoleEnum
from backend.app.schemas.phase10_revision import (
    FlashcardDeckCreate, FlashcardDeckResponse,
    FlashcardItemCreate, FlashcardItemResponse,
    CardReviewSubmitRequest, CardReviewSubmitResponse,
    FocusSessionStartRequest, FocusSessionHeartbeatRequest, FocusSessionResponse,
    MistakeEntryCreate, MistakeEntryResponse,
    RevisionDashboardStats, AnkiImportPayload, AnkiExportPayload
)
from backend.app.services.revision_service import RevisionService

router = APIRouter(prefix="/revision", tags=["Smart Revision & Spaced Repetition"])

# --- Decks ---

@router.post("/decks", response_model=FlashcardDeckResponse, status_code=status.HTTP_201_CREATED)
async def create_deck(
    payload: FlashcardDeckCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    deck = await RevisionService.create_deck(db, current_user.id, payload)
    return FlashcardDeckResponse(
        id=deck.id,
        user_id=deck.user_id,
        title=deck.title,
        description=deck.description,
        category=deck.category,
        tags=deck.tags or [],
        is_public=deck.is_public,
        is_system=deck.is_system,
        is_approved=deck.is_approved,
        is_archived=deck.is_archived,
        share_slug=deck.share_slug,
        card_count=0,
        due_card_count=0,
        created_at=deck.created_at,
        updated_at=deck.updated_at
    )

@router.get("/decks", response_model=List[FlashcardDeckResponse])
async def list_decks(
    category: Optional[str] = None,
    include_public: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    return await RevisionService.list_decks(db, current_user.id, category=category, include_public=include_public)

@router.get("/decks/{deck_id}", response_model=FlashcardDeckResponse)
async def get_deck_detail(
    deck_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    deck = await RevisionService.get_deck(db, deck_id, current_user.id)
    return FlashcardDeckResponse(
        id=deck.id,
        user_id=deck.user_id,
        title=deck.title,
        description=deck.description,
        category=deck.category,
        tags=deck.tags or [],
        is_public=deck.is_public,
        is_system=deck.is_system,
        is_approved=deck.is_approved,
        is_archived=deck.is_archived,
        share_slug=deck.share_slug,
        card_count=0,
        due_card_count=0,
        created_at=deck.created_at,
        updated_at=deck.updated_at
    )

@router.post("/decks/{deck_id}/fork", response_model=FlashcardDeckResponse, status_code=status.HTTP_201_CREATED)
async def fork_deck(
    deck_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """FEAT-161: Fork a public deck into the current user's library."""
    forked = await RevisionService.fork_deck(db, current_user.id, deck_id)
    return FlashcardDeckResponse(
        id=forked.id,
        user_id=forked.user_id,
        title=forked.title,
        description=forked.description,
        category=forked.category,
        tags=forked.tags or [],
        is_public=forked.is_public,
        is_system=forked.is_system,
        is_approved=forked.is_approved,
        is_archived=forked.is_archived,
        share_slug=forked.share_slug,
        card_count=0,
        due_card_count=0,
        created_at=forked.created_at,
        updated_at=forked.updated_at
    )

@router.get("/admin/moderation/pending", response_model=List[FlashcardDeckResponse])
async def list_pending_moderation_decks(
    admin: User = Depends(require_roles([UserRoleEnum.ADMIN])),
    db: AsyncSession = Depends(get_db_session)
):
    """FEAT-162: Admin lists public decks awaiting moderation."""
    decks = await RevisionService.list_pending_decks_for_moderation(db)
    return [
        FlashcardDeckResponse(
            id=d.id,
            user_id=d.user_id,
            title=d.title,
            description=d.description,
            category=d.category,
            tags=d.tags or [],
            is_public=d.is_public,
            is_system=d.is_system,
            is_approved=d.is_approved,
            is_archived=d.is_archived,
            share_slug=d.share_slug,
            card_count=0,
            due_card_count=0,
            created_at=d.created_at,
            updated_at=d.updated_at
        )
        for d in decks
    ]

@router.post("/admin/moderation/{deck_id}/approve", response_model=FlashcardDeckResponse)
async def approve_deck(
    deck_id: str,
    admin: User = Depends(require_roles([UserRoleEnum.ADMIN])),
    db: AsyncSession = Depends(get_db_session)
):
    """FEAT-162: Admin approves a community deck."""
    deck = await RevisionService.moderate_deck(db, deck_id, approved=True)
    return FlashcardDeckResponse(
        id=deck.id,
        user_id=deck.user_id,
        title=deck.title,
        description=deck.description,
        category=deck.category,
        tags=deck.tags or [],
        is_public=deck.is_public,
        is_system=deck.is_system,
        is_approved=deck.is_approved,
        is_archived=deck.is_archived,
        share_slug=deck.share_slug,
        card_count=0,
        due_card_count=0,
        created_at=deck.created_at,
        updated_at=deck.updated_at
    )

@router.post("/admin/moderation/{deck_id}/reject", response_model=FlashcardDeckResponse)
async def reject_deck(
    deck_id: str,
    admin: User = Depends(require_roles([UserRoleEnum.ADMIN])),
    db: AsyncSession = Depends(get_db_session)
):
    """FEAT-162: Admin rejects a community deck."""
    deck = await RevisionService.moderate_deck(db, deck_id, approved=False)
    return FlashcardDeckResponse(
        id=deck.id,
        user_id=deck.user_id,
        title=deck.title,
        description=deck.description,
        category=deck.category,
        tags=deck.tags or [],
        is_public=deck.is_public,
        is_system=deck.is_system,
        is_approved=deck.is_approved,
        is_archived=deck.is_archived,
        share_slug=deck.share_slug,
        card_count=0,
        due_card_count=0,
        created_at=deck.created_at,
        updated_at=deck.updated_at
    )

# --- Cards ---

@router.post("/decks/{deck_id}/cards", response_model=FlashcardItemResponse, status_code=status.HTTP_201_CREATED)
async def add_card(
    deck_id: str,
    payload: FlashcardItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    card = await RevisionService.add_card(db, current_user.id, deck_id, payload)
    return FlashcardItemResponse(
        id=card.id,
        deck_id=card.deck_id,
        prompt=card.prompt,
        answer=card.answer,
        explanation=card.explanation,
        code_snippet=card.code_snippet,
        audio_url=card.audio_url,
        order_index=card.order_index,
        created_at=card.created_at,
        repetition=0,
        interval_days=0,
        ease_factor=2.50,
        stability=1.00,
        next_review_at=None,
        is_due=True
    )

@router.get("/cards/due", response_model=List[FlashcardItemResponse])
async def get_due_cards(
    deck_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    return await RevisionService.get_due_cards(db, current_user.id, deck_id=deck_id, limit=limit)

# --- Reviews (SM-2 & Idempotency) ---

@router.post("/reviews/submit", response_model=CardReviewSubmitResponse)
async def submit_card_review(
    payload: CardReviewSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    return await RevisionService.submit_card_review(db, current_user.id, payload)

# --- Dashboard & Heatmap ---

@router.get("/dashboard/stats", response_model=RevisionDashboardStats)
async def get_dashboard_stats(
    timezone: Optional[str] = Query("UTC"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    return await RevisionService.get_dashboard_stats(db, current_user.id, user_tz_name=timezone or "UTC")

# --- Focus Sessions ---

@router.post("/focus/start", response_model=FocusSessionResponse)
async def start_focus_session(
    payload: FocusSessionStartRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    return await RevisionService.start_focus_session(db, current_user.id, payload.deck_id, payload.duration_minutes)

@router.post("/focus/{session_id}/heartbeat", response_model=FocusSessionResponse)
async def heartbeat_focus_session(
    session_id: str,
    payload: FocusSessionHeartbeatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    return await RevisionService.heartbeat_focus_session(
        db, current_user.id, session_id, payload.elapsed_seconds, payload.cards_reviewed, payload.status
    )

# --- Mistake Notebook ---

@router.post("/mistakes", response_model=MistakeEntryResponse, status_code=status.HTTP_201_CREATED)
async def add_mistake_entry(
    payload: MistakeEntryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    return await RevisionService.add_mistake_entry(db, current_user.id, payload)

@router.get("/mistakes", response_model=List[MistakeEntryResponse])
async def list_mistakes(
    resolved: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    return await RevisionService.list_mistakes(db, current_user.id, resolved=resolved)

@router.post("/mistakes/{mistake_id}/resolve", response_model=MistakeEntryResponse)
async def resolve_mistake(
    mistake_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    return await RevisionService.resolve_mistake(db, current_user.id, mistake_id)

# --- Anki Import / Export ---

@router.get("/decks/{deck_id}/export/anki", response_model=AnkiExportPayload)
async def export_deck_anki(
    deck_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    return await RevisionService.export_deck_anki(db, current_user.id, deck_id)

@router.post("/decks/import/anki", response_model=FlashcardDeckResponse)
async def import_deck_anki(
    payload: AnkiImportPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    deck = await RevisionService.import_deck_anki(db, current_user.id, payload)
    return FlashcardDeckResponse(
        id=deck.id,
        user_id=deck.user_id,
        title=deck.title,
        description=deck.description,
        category=deck.category,
        tags=deck.tags or [],
        is_public=deck.is_public,
        is_system=deck.is_system,
        is_approved=deck.is_approved,
        is_archived=deck.is_archived,
        share_slug=deck.share_slug,
        card_count=len(payload.cards),
        due_card_count=len(payload.cards),
        created_at=deck.created_at,
        updated_at=deck.updated_at
    )
