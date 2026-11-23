from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.app.db.session import get_db_session
from backend.app.api.deps import get_current_user
from backend.app.models.auth import User, StudentProfile
from backend.app.models.phase10_revision import (
    FlashcardDeck, FlashcardItem, StudentCardReview, MistakeNotebookEntry
)
from backend.app.schemas.phase10_revision import CardReviewSubmitRequest
from backend.app.schemas.phase11_sync import (
    SyncPushRequest, SyncPushResponse, SyncOperationResult,
    SyncPullResponse, SyncSnapshotResponse
)
from backend.app.services.sync_service import SyncService
from backend.app.services.revision_service import RevisionService
from backend.app.core.logging import logger

router = APIRouter(prefix="/sync", tags=["Mobile & Cross-Device Synchronization Engine"])


@router.post("/push", response_model=SyncPushResponse)
async def sync_push_operations(
    payload: SyncPushRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Submits a batch of offline student actions (reviews, mistake resolutions).
    Atomically processes operations using server-acceptance ordering and idempotent replays.
    """
    results: List[SyncOperationResult] = []

    for op in payload.operations:
        if op.action_type == "SUBMIT_CARD_REVIEW":
            p = op.payload
            card_id = p.get("card_id")
            grade = p.get("grade")
            if not card_id or grade is None or not (0 <= grade <= 5):
                results.append(SyncOperationResult(
                    op_id=op.op_id,
                    status="REJECTED",
                    message="Invalid card_id or grade"
                ))
                continue

            review_req = CardReviewSubmitRequest(
                card_id=card_id,
                grade=grade,
                idempotency_key=op.op_id,
                session_id=p.get("session_id"),
                time_spent_ms=p.get("time_spent_ms", 0),
                user_timezone=p.get("user_timezone", "UTC"),
                base_state_version=p.get("base_state_version"),
                device_id=payload.device_id,
                client_reviewed_at=op.client_timestamp
            )

            try:
                review_resp = await RevisionService.submit_card_review(
                    db=db,
                    user_id=current_user.id,
                    req=review_req
                )
                results.append(SyncOperationResult(
                    op_id=op.op_id,
                    status="REPLAYED" if review_resp.is_replayed else ("SUPERSEDED" if review_resp.is_superseded else "SUCCESS"),
                    card_id=review_resp.card_id,
                    repetition=review_resp.repetition,
                    interval_days=review_resp.interval_days,
                    ease_factor=review_resp.ease_factor,
                    stability=review_resp.stability,
                    next_review_at=review_resp.next_review_at.isoformat(),
                    resulting_state_version=review_resp.resulting_state_version,
                    is_replayed=review_resp.is_replayed,
                    is_superseded=review_resp.is_superseded
                ))
            except HTTPException as he:
                results.append(SyncOperationResult(
                    op_id=op.op_id,
                    status="REJECTED",
                    message=str(he.detail)
                ))
            except Exception as e:
                logger.error(f"Error processing offline review op {op.op_id}: {str(e)}")
                results.append(SyncOperationResult(
                    op_id=op.op_id,
                    status="REJECTED",
                    message=f"Internal error: {str(e)}"
                ))
        else:
            results.append(SyncOperationResult(
                op_id=op.op_id,
                status="REJECTED",
                message=f"Unsupported action_type: {op.action_type}"
            ))

    await db.commit()

    counter = await SyncService.get_or_create_counter(db, current_user.id)
    return SyncPushResponse(
        device_id=payload.device_id,
        processed_count=len(results),
        results=results,
        new_server_seq=counter.current_val
    )


@router.get("/pull", response_model=SyncPullResponse)
async def sync_pull_deltas(
    device_id: str = Query(..., min_length=1, max_length=100),
    since_seq: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Retrieves deltas committed after since_seq strictly ordered by change_seq ASC.
    Validates 90-day retention boundary (HTTP 410 if expired).
    """
    res = await SyncService.pull_deltas(
        db=db,
        user_id=current_user.id,
        device_id=device_id,
        since_seq=since_seq,
        limit=limit
    )
    await db.commit()
    return res


@router.get("/snapshot", response_model=SyncSnapshotResponse)
async def sync_full_snapshot(
    device_id: str = Query(..., min_length=1, max_length=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Generates a consistent base snapshot for new client devices or recovery after retention expiry.
    Captures snapshot_seq atomically so all subsequent commits have change_seq > snapshot_seq.
    """
    counter = await SyncService.get_or_create_counter(db, current_user.id)
    snapshot_seq = counter.current_val

    # 1. Fetch user decks
    decks_stmt = select(FlashcardDeck).where(
        FlashcardDeck.user_id == current_user.id,
        FlashcardDeck.is_archived == False
    )
    decks = (await db.execute(decks_stmt)).scalars().all()

    # 2. Fetch due / active cards
    cards_stmt = (
        select(FlashcardItem, StudentCardReview)
        .join(FlashcardDeck, FlashcardItem.deck_id == FlashcardDeck.id)
        .outerjoin(
            StudentCardReview,
            (StudentCardReview.card_id == FlashcardItem.id) & (StudentCardReview.user_id == current_user.id)
        )
        .where(
            FlashcardDeck.user_id == current_user.id,
            FlashcardDeck.is_archived == False
        )
    )
    card_rows = (await db.execute(cards_stmt)).all()

    # 3. Fetch readiness score
    prof_stmt = select(StudentProfile.readiness_score).where(StudentProfile.user_id == current_user.id)
    readiness = (await db.execute(prof_stmt)).scalar_one_or_none() or 0

    # 4. Fetch unresolved mistakes
    mistakes_stmt = select(MistakeNotebookEntry).where(
        MistakeNotebookEntry.user_id == current_user.id,
        MistakeNotebookEntry.is_resolved == False
    )
    mistakes = (await db.execute(mistakes_stmt)).scalars().all()

    return SyncSnapshotResponse(
        snapshot_seq=snapshot_seq,
        decks=[
            {"id": d.id, "title": d.title, "category": d.category}
            for d in decks
        ],
        due_cards=[
            {
                "id": card.id,
                "deck_id": card.deck_id,
                "prompt": card.prompt,
                "answer": card.answer,
                "state_version": rev.state_version if rev else 1,
                "interval_days": rev.interval_days if rev else 0,
                "ease_factor": rev.ease_factor if rev else 2.50
            }
            for card, rev in card_rows
        ],
        readiness_score=readiness,
        mistakes=[
            {"id": m.id, "title": m.title, "source_type": m.source_type}
            for m in mistakes
        ],
        generated_at=datetime.now(timezone.utc)
    )
