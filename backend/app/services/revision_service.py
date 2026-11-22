import hashlib
import json
import uuid
import zoneinfo
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, text, and_, or_, desc
from sqlalchemy.dialects.postgresql import insert

from fastapi import HTTPException, status
from backend.app.models.phase10_revision import (
    FlashcardDeck, FlashcardItem, StudentCardReview, StudentCardReviewLog,
    MistakeNotebookEntry, RevisionFocusSession
)
from backend.app.models.auth import StudentProfile
from backend.app.schemas.phase10_revision import (
    FlashcardDeckCreate, FlashcardDeckUpdate, FlashcardItemCreate, FlashcardItemUpdate,
    CardReviewSubmitRequest, CardReviewSubmitResponse, MistakeEntryCreate,
    AnkiImportPayload, AnkiExportPayload, AnkiExportCard
)
from backend.app.services.sm2_service import SM2Engine, SM2CalculationResult

class RevisionService:

    @staticmethod
    def _compute_request_hash(user_id: str, card_id: str, grade: int, session_id: Optional[str], time_spent_ms: int, user_tz: str) -> str:
        canonical_str = f"{user_id}:{card_id}:{grade}:{session_id or ''}:{time_spent_ms}:{user_tz}"
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    # --- Deck Operations ---

    @classmethod
    async def create_deck(cls, db: AsyncSession, user_id: str, data: FlashcardDeckCreate) -> FlashcardDeck:
        share_slug = str(uuid.uuid4())[:8] if data.is_public else None
        deck = FlashcardDeck(
            user_id=user_id,
            title=data.title,
            description=data.description,
            category=data.category,
            tags=data.tags,
            is_public=data.is_public,
            is_approved=False,  # Moderation gate
            is_system=False,
            is_archived=False,
            share_slug=share_slug
        )
        db.add(deck)
        await db.commit()
        await db.refresh(deck)
        return deck

    @classmethod
    async def fork_deck(cls, db: AsyncSession, user_id: str, deck_id: str) -> FlashcardDeck:
        """
        FEAT-161: Fork a public approved deck or accessible deck into the user's private library.
        Creates an independent clone of the deck and all its flashcard items.
        """
        source_deck = await cls.get_deck(db, deck_id, user_id)
        if not source_deck.is_public and source_deck.user_id != user_id:
            raise HTTPException(status_code=403, detail="Cannot fork a private deck belonging to another user.")

        forked_deck = FlashcardDeck(
            user_id=user_id,
            title=f"{source_deck.title} (Forked)",
            description=source_deck.description,
            category=source_deck.category,
            tags=list(source_deck.tags or []) + ["forked"],
            is_public=False,
            is_approved=False,
            is_system=False,
            is_archived=False,
            share_slug=None
        )
        db.add(forked_deck)
        await db.flush()

        # Copy all cards independently
        cards = (await db.execute(
            select(FlashcardItem).where(FlashcardItem.deck_id == source_deck.id).order_by(FlashcardItem.order_index)
        )).scalars().all()

        for c in cards:
            new_card = FlashcardItem(
                deck_id=forked_deck.id,
                prompt=c.prompt,
                answer=c.answer,
                explanation=c.explanation,
                code_snippet=c.code_snippet,
                audio_url=c.audio_url,
                order_index=c.order_index
            )
            db.add(new_card)

        await db.commit()
        await db.refresh(forked_deck)
        return forked_deck

    @classmethod
    async def list_pending_decks_for_moderation(cls, db: AsyncSession) -> List[FlashcardDeck]:
        """
        FEAT-162: List all public decks awaiting admin approval.
        """
        stmt = select(FlashcardDeck).where(
            FlashcardDeck.is_public == True,
            FlashcardDeck.is_approved == False,
            FlashcardDeck.is_archived == False
        ).order_by(desc(FlashcardDeck.created_at))
        return (await db.execute(stmt)).scalars().all()

    @classmethod
    async def moderate_deck(cls, db: AsyncSession, deck_id: str, approved: bool) -> FlashcardDeck:
        """
        FEAT-162: Admin approves or rejects a community deck.
        """
        deck = (await db.execute(select(FlashcardDeck).where(FlashcardDeck.id == deck_id))).scalar_one_or_none()
        if not deck:
            raise HTTPException(status_code=404, detail="Flashcard deck not found")

        deck.is_approved = approved
        if not approved:
            deck.is_public = False  # Revoke public visibility if rejected
        await db.commit()
        await db.refresh(deck)
        return deck

    @classmethod
    async def list_decks(cls, db: AsyncSession, user_id: str, category: Optional[str] = None, include_public: bool = False) -> List[Dict[str, Any]]:
        query = select(FlashcardDeck).where(
            FlashcardDeck.is_archived == False
        )
        if include_public:
            query = query.where(
                or_(
                    FlashcardDeck.user_id == user_id,
                    and_(FlashcardDeck.is_public == True, FlashcardDeck.is_approved == True)
                )
            )
        else:
            query = query.where(FlashcardDeck.user_id == user_id)

        if category:
            query = query.where(FlashcardDeck.category == category)

        query = query.order_by(desc(FlashcardDeck.created_at))
        result = await db.execute(query)
        decks = result.scalars().all()

        now = datetime.now(timezone.utc)
        deck_list = []
        for d in decks:
            # Count total cards
            c_cnt = (await db.execute(
                select(func.count(FlashcardItem.id)).where(FlashcardItem.deck_id == d.id)
            )).scalar() or 0

            # Count due cards for this user
            due_sub = select(FlashcardItem.id).where(FlashcardItem.deck_id == d.id).subquery()
            reviewed_due = (await db.execute(
                select(func.count(StudentCardReview.id)).where(
                    StudentCardReview.user_id == user_id,
                    StudentCardReview.card_id.in_(select(due_sub)),
                    StudentCardReview.next_review_at <= now
                )
            )).scalar() or 0

            unreviewed = (await db.execute(
                select(func.count(FlashcardItem.id)).where(
                    FlashcardItem.deck_id == d.id,
                    ~FlashcardItem.id.in_(
                        select(StudentCardReview.card_id).where(StudentCardReview.user_id == user_id)
                    )
                )
            )).scalar() or 0

            deck_list.append({
                "id": d.id,
                "user_id": d.user_id,
                "title": d.title,
                "description": d.description,
                "category": d.category,
                "tags": d.tags or [],
                "is_public": d.is_public,
                "is_system": d.is_system,
                "is_approved": d.is_approved,
                "is_archived": d.is_archived,
                "share_slug": d.share_slug,
                "card_count": c_cnt,
                "due_card_count": reviewed_due + unreviewed,
                "created_at": d.created_at,
                "updated_at": d.updated_at
            })
        return deck_list

    @classmethod
    async def get_deck(cls, db: AsyncSession, deck_id: str, user_id: str) -> FlashcardDeck:
        deck = (await db.execute(select(FlashcardDeck).where(FlashcardDeck.id == deck_id))).scalar_one_or_none()
        if not deck:
            raise HTTPException(status_code=404, detail="Flashcard deck not found")
        if deck.user_id != user_id and not (deck.is_public and deck.is_approved):
            raise HTTPException(status_code=403, detail="Access denied to private deck")
        return deck

    # --- Card Operations ---

    @classmethod
    async def add_card(cls, db: AsyncSession, user_id: str, deck_id: str, data: FlashcardItemCreate) -> FlashcardItem:
        deck = await cls.get_deck(db, deck_id, user_id)
        if deck.user_id != user_id:
            raise HTTPException(status_code=403, detail="Cannot add cards to another user's deck")

        card = FlashcardItem(
            deck_id=deck_id,
            prompt=data.prompt,
            answer=data.answer,
            explanation=data.explanation,
            code_snippet=data.code_snippet,
            audio_url=data.audio_url,
            order_index=data.order_index
        )
        db.add(card)
        await db.commit()
        await db.refresh(card)
        return card

    @classmethod
    async def get_due_cards(cls, db: AsyncSession, user_id: str, deck_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        now = datetime.now(timezone.utc)
        
        # Build query for cards in deck(s)
        base_query = select(FlashcardItem, StudentCardReview).outerjoin(
            StudentCardReview,
            and_(
                StudentCardReview.card_id == FlashcardItem.id,
                StudentCardReview.user_id == user_id
            )
        )
        if deck_id:
            base_query = base_query.where(FlashcardItem.deck_id == deck_id)
        
        # Due filter: either never reviewed (StudentCardReview is NULL) or next_review_at <= now
        base_query = base_query.where(
            or_(
                StudentCardReview.id == None,
                StudentCardReview.next_review_at <= now
            )
        ).order_by(
            func.coalesce(StudentCardReview.next_review_at, now),
            FlashcardItem.order_index
        ).limit(limit)

        result = await db.execute(base_query)
        items = []
        for card, review in result.all():
            items.append({
                "id": card.id,
                "deck_id": card.deck_id,
                "prompt": card.prompt,
                "answer": card.answer,
                "explanation": card.explanation,
                "code_snippet": card.code_snippet,
                "audio_url": card.audio_url,
                "order_index": card.order_index,
                "created_at": card.created_at,
                "repetition": review.repetition if review else 0,
                "interval_days": review.interval_days if review else 0,
                "ease_factor": review.ease_factor if review else 2.50,
                "stability": review.stability if review else 1.00,
                "next_review_at": review.next_review_at if review else None,
                "is_due": True
            })
        return items

    # --- Review Submission with Atomic Idempotency & Pre-seed Lock ---

    @classmethod
    async def submit_card_review(cls, db: AsyncSession, user_id: str, req: CardReviewSubmitRequest) -> CardReviewSubmitResponse:
        now = datetime.now(timezone.utc)
        req_hash = cls._compute_request_hash(user_id, req.card_id, req.grade, req.session_id, req.time_spent_ms, req.user_timezone or "UTC")

        # 1. Check existing idempotency record
        existing_log_stmt = select(StudentCardReviewLog).where(
            StudentCardReviewLog.user_id == user_id,
            StudentCardReviewLog.idempotency_key == req.idempotency_key
        )
        existing_log = (await db.execute(existing_log_stmt)).scalar_one_or_none()
        if existing_log:
            if existing_log.request_hash == req_hash:
                # Exact replay
                payload = existing_log.response_payload
                return CardReviewSubmitResponse(
                    idempotency_key=req.idempotency_key,
                    card_id=req.card_id,
                    submitted_grade=req.grade,
                    repetition=payload["repetition"],
                    interval_days=payload["interval_days"],
                    ease_factor=payload["ease_factor"],
                    stability=payload["stability"],
                    next_review_at=datetime.fromisoformat(payload["next_review_at"]),
                    is_replayed=True
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Idempotency key reused with conflicting request payload."
                )

        # 2. Verify card exists
        card = (await db.execute(select(FlashcardItem).where(FlashcardItem.id == req.card_id))).scalar_one_or_none()
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")

        # 3. Pre-seed review record atomically using ON CONFLICT DO NOTHING to handle first review concurrency
        preseed_stmt = insert(StudentCardReview).values(
            id=str(uuid.uuid4()),
            user_id=user_id,
            card_id=req.card_id,
            repetition=0,
            interval_days=0,
            ease_factor=2.50,
            stability=1.00,
            next_review_at=now,
            last_reviewed_at=None
        ).on_conflict_do_nothing(index_elements=["user_id", "card_id"])
        await db.execute(preseed_stmt)
        await db.flush()

        # 4. Lock row with SELECT ... FOR UPDATE
        lock_stmt = select(StudentCardReview).where(
            StudentCardReview.user_id == user_id,
            StudentCardReview.card_id == req.card_id
        ).with_for_update()
        review = (await db.execute(lock_stmt)).scalar_one()

        # 5. Capture EXACT PREVIOUS VALUES before mutation
        prev_rep = review.repetition
        prev_interval = review.interval_days
        prev_ef = review.ease_factor
        prev_stability = review.stability
        prev_next_review_at = review.next_review_at

        # 6. Calculate new values with SM-2 Engine
        calc: SM2CalculationResult = SM2Engine.calculate(
            current_repetition=prev_rep,
            current_interval=prev_interval,
            current_ease_factor=prev_ef,
            current_stability=prev_stability,
            grade=req.grade,
            review_time=now
        )

        # 7. Mutate current review record
        review.repetition = calc.repetition
        review.interval_days = calc.interval_days
        review.ease_factor = calc.ease_factor
        review.stability = calc.stability
        review.next_review_at = calc.next_review_at
        review.last_reviewed_at = now

        response_payload = {
            "repetition": calc.repetition,
            "interval_days": calc.interval_days,
            "ease_factor": calc.ease_factor,
            "stability": calc.stability,
            "next_review_at": calc.next_review_at.isoformat()
        }

        # 8. Insert immutable audit log
        log_entry = StudentCardReviewLog(
            user_id=user_id,
            card_id=req.card_id,
            review_id=review.id,
            session_id=req.session_id,
            idempotency_key=req.idempotency_key,
            request_hash=req_hash,
            submitted_grade=req.grade,
            time_spent_ms=req.time_spent_ms,
            prev_repetition=prev_rep,
            new_repetition=calc.repetition,
            prev_interval=prev_interval,
            new_interval=calc.interval_days,
            prev_ease_factor=prev_ef,
            new_ease_factor=calc.ease_factor,
            prev_stability=prev_stability,
            new_stability=calc.stability,
            prev_next_review_at=prev_next_review_at,
            new_next_review_at=calc.next_review_at,
            response_payload=response_payload,
            reviewed_at=now
        )
        db.add(log_entry)

        # 9. Update focus session card count if session_id provided
        if req.session_id:
            sess_stmt = select(RevisionFocusSession).where(
                RevisionFocusSession.id == req.session_id,
                RevisionFocusSession.user_id == user_id
            )
            sess = (await db.execute(sess_stmt)).scalar_one_or_none()
            if sess and sess.status == "IN_PROGRESS":
                sess.cards_reviewed += 1

        await db.commit()

        return CardReviewSubmitResponse(
            idempotency_key=req.idempotency_key,
            card_id=req.card_id,
            submitted_grade=req.grade,
            repetition=calc.repetition,
            interval_days=calc.interval_days,
            ease_factor=calc.ease_factor,
            stability=calc.stability,
            next_review_at=calc.next_review_at,
            is_replayed=False
        )

    # --- Heatmap and Dashboard Analytics ---

    @classmethod
    async def get_dashboard_stats(cls, db: AsyncSession, user_id: str, user_tz_name: str = "UTC") -> Dict[str, Any]:
        # Validate timezone safely without relying on tzdata package on Windows
        tz_obj = timezone.utc
        if user_tz_name and user_tz_name.upper() != "UTC":
            try:
                import zoneinfo
                tz_obj = zoneinfo.ZoneInfo(user_tz_name)
            except Exception:
                tz_obj = timezone.utc
                user_tz_name = "UTC"
        else:
            user_tz_name = "UTC"

        now = datetime.now(timezone.utc)

        # Total decks & cards
        total_decks = (await db.execute(select(func.count(FlashcardDeck.id)).where(FlashcardDeck.user_id == user_id, FlashcardDeck.is_archived == False))).scalar() or 0
        total_cards = (await db.execute(select(func.count(FlashcardItem.id)).join(FlashcardDeck).where(FlashcardDeck.user_id == user_id))).scalar() or 0

        # Due cards count
        due_cards = len(await cls.get_due_cards(db, user_id, limit=5000))

        # Reviews today in user timezone
        # Group by 365 days
        one_year_ago = now - timedelta(days=365)
        heatmap_stmt = text("""
            SELECT TO_CHAR(reviewed_at AT TIME ZONE :tz, 'YYYY-MM-DD') AS day_str, count(*) as cnt
            FROM student_card_review_logs
            WHERE user_id = :user_id AND reviewed_at >= :one_year_ago
            GROUP BY day_str
            ORDER BY day_str ASC
        """)
        heatmap_res = (await db.execute(heatmap_stmt, {"tz": user_tz_name, "user_id": user_id, "one_year_ago": one_year_ago})).fetchall()
        heatmap_dict = {row.day_str: row.cnt for row in heatmap_res}

        # Calculate today's reviews in user timezone
        today_date = datetime.now(tz_obj).date()
        today_str = today_date.strftime("%Y-%m-%d")
        cards_reviewed_today = heatmap_dict.get(today_str, 0)

        # Compute streak
        streak = 0
        curr_date = today_date
        while True:
            d_str = curr_date.strftime("%Y-%m-%d")
            if heatmap_dict.get(d_str, 0) > 0:
                streak += 1
                curr_date -= timedelta(days=1)
            else:
                # If today hasn't been reviewed yet, check if yesterday was part of streak
                if streak == 0 and curr_date == today_date:
                    curr_date -= timedelta(days=1)
                    continue
                break

        # Calculate average retention rate across reviewed cards
        avg_retention_stmt = select(func.avg(StudentCardReview.stability), func.count(StudentCardReview.id)).where(
            StudentCardReview.user_id == user_id
        )
        avg_stab_res = (await db.execute(avg_retention_stmt)).first()
        avg_stability = avg_stab_res[0] or 1.0
        review_count = avg_stab_res[1] or 0
        retention_rate = round(SM2Engine.calculate_retention_probability(avg_stability, 1.0) * 100.0, 1) if review_count > 0 else 100.0

        # Build zero-filled 365-day heatmap list
        heatmap_list = []
        for i in range(365, -1, -1):
            day_key = (today_date - timedelta(days=i)).strftime("%Y-%m-%d")
            heatmap_list.append({
                "date": day_key,
                "count": heatmap_dict.get(day_key, 0)
            })

        return {
            "total_decks": total_decks,
            "total_cards": total_cards,
            "due_cards_count": due_cards,
            "cards_reviewed_today": cards_reviewed_today,
            "retention_rate_pct": retention_rate,
            "current_streak_days": streak,
            "heatmap": heatmap_list
        }

    # --- Mistake Notebook ---

    @classmethod
    async def add_mistake_entry(cls, db: AsyncSession, user_id: str, data: MistakeEntryCreate) -> MistakeNotebookEntry:
        entry = MistakeNotebookEntry(
            user_id=user_id,
            source_type=data.source_type,
            source_id=data.source_id,
            title=data.title,
            question_context=data.question_context,
            submitted_answer=data.submitted_answer,
            expected_answer=data.expected_answer,
            error_message=data.error_message,
            tags=data.tags or [],
            is_resolved=False
        )
        db.add(entry)
        await db.commit()
        await db.refresh(entry)
        return entry

    @classmethod
    async def list_mistakes(cls, db: AsyncSession, user_id: str, resolved: Optional[bool] = None) -> List[MistakeNotebookEntry]:
        query = select(MistakeNotebookEntry).where(MistakeNotebookEntry.user_id == user_id)
        if resolved is not None:
            query = query.where(MistakeNotebookEntry.is_resolved == resolved)
        query = query.order_by(desc(MistakeNotebookEntry.created_at))
        return (await db.execute(query)).scalars().all()

    @classmethod
    async def resolve_mistake(cls, db: AsyncSession, user_id: str, mistake_id: str) -> MistakeNotebookEntry:
        entry = (await db.execute(select(MistakeNotebookEntry).where(MistakeNotebookEntry.id == mistake_id, MistakeNotebookEntry.user_id == user_id))).scalar_one_or_none()
        if not entry:
            raise HTTPException(status_code=404, detail="Mistake entry not found")
        entry.is_resolved = True
        entry.resolved_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(entry)
        return entry

    # --- Focus Session Management ---

    @classmethod
    async def start_focus_session(cls, db: AsyncSession, user_id: str, deck_id: Optional[str], duration_minutes: int) -> RevisionFocusSession:
        session = RevisionFocusSession(
            user_id=user_id,
            deck_id=deck_id,
            duration_minutes=duration_minutes,
            elapsed_seconds=0,
            cards_reviewed=0,
            status="IN_PROGRESS"
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @classmethod
    async def heartbeat_focus_session(cls, db: AsyncSession, user_id: str, session_id: str, elapsed_seconds: int, cards_reviewed: int, status_str: str) -> RevisionFocusSession:
        session = (await db.execute(select(RevisionFocusSession).where(RevisionFocusSession.id == session_id, RevisionFocusSession.user_id == user_id))).scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Focus session not found")
        session.elapsed_seconds = elapsed_seconds
        session.cards_reviewed = max(session.cards_reviewed, cards_reviewed)
        if status_str in ["COMPLETED", "ABORTED"]:
            session.status = status_str
            session.ended_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(session)
        return session

    # --- Anki Import / Export ---

    @classmethod
    async def export_deck_anki(cls, db: AsyncSession, user_id: str, deck_id: str) -> AnkiExportPayload:
        deck = await cls.get_deck(db, deck_id, user_id)
        cards = (await db.execute(select(FlashcardItem).where(FlashcardItem.deck_id == deck_id).order_by(FlashcardItem.order_index))).scalars().all()
        export_cards = [
            AnkiExportCard(
                prompt=c.prompt,
                answer=c.answer,
                explanation=c.explanation,
                tags=deck.tags or []
            )
            for c in cards
        ]
        return AnkiExportPayload(deck_title=deck.title, cards=export_cards)

    @classmethod
    async def import_deck_anki(cls, db: AsyncSession, user_id: str, payload: AnkiImportPayload) -> FlashcardDeck:
        title = payload.title or payload.deck_title or "Imported Flashcard Deck"
        category = payload.category or "Anki Import"
        description = payload.description or "Imported from Anki JSON format"

        deck = FlashcardDeck(
            user_id=user_id,
            title=title,
            description=description,
            category=category,
            tags=["anki-import"],
            is_public=False,
            is_approved=False
        )
        db.add(deck)
        await db.flush()

        for idx, c in enumerate(payload.cards):
            item = FlashcardItem(
                deck_id=deck.id,
                prompt=c.prompt,
                answer=c.answer,
                explanation=c.explanation,
                order_index=idx
            )
            db.add(item)

        await db.commit()
        await db.refresh(deck)
        return deck
