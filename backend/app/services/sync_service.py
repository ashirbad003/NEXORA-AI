import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, delete, text
from fastapi import HTTPException, status

from backend.app.models.phase11_sync import (
    UserSyncCounter, UserSyncChangeFeed, UserSyncTombstone, UserSyncWatermark
)
from backend.app.core.logging import logger


class SyncService:
    """
    Core sequence allocation, change feed, and synchronization engine.
    Ensures per-user strictly monotonic sequence ordering via PostgreSQL row-level locks.
    """

    @classmethod
    async def get_or_create_counter(cls, db: AsyncSession, user_id: str) -> UserSyncCounter:
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        # Atomic ON CONFLICT DO NOTHING to prevent race conditions during concurrent counter initialization
        insert_stmt = (
            pg_insert(UserSyncCounter)
            .values(
                user_id=user_id,
                current_val=0,
                min_available_seq=1,
                updated_at=datetime.now(timezone.utc)
            )
            .on_conflict_do_nothing(index_elements=["user_id"])
        )
        await db.execute(insert_stmt)
        await db.flush()

        stmt = select(UserSyncCounter).where(UserSyncCounter.user_id == user_id)
        return (await db.execute(stmt)).scalar_one()

    @classmethod
    async def allocate_sequences(cls, db: AsyncSession, user_id: str, count: int = 1) -> List[int]:
        """
        Acquires exclusive row lock on user_sync_counters with SELECT ... FOR UPDATE.
        Increments current_val by count and returns contiguous list of allocated sequences.
        """
        # Ensure row exists
        await cls.get_or_create_counter(db, user_id)

        lock_stmt = (
            select(UserSyncCounter)
            .where(UserSyncCounter.user_id == user_id)
            .with_for_update()
        )
        counter = (await db.execute(lock_stmt)).scalar_one()

        start_seq = counter.current_val + 1
        counter.current_val += count
        counter.updated_at = datetime.now(timezone.utc)
        await db.flush()

        return list(range(start_seq, start_seq + count))

    @classmethod
    async def append_change_event(
        cls,
        db: AsyncSession,
        user_id: str,
        entity_type: str,
        entity_id: str,
        operation: str,
        payload: Dict[str, Any],
        allocated_seq: Optional[int] = None
    ) -> UserSyncChangeFeed:
        """
        Records an append-only mutation event in user_sync_change_feed.
        Must be invoked in the exact same database transaction as the domain mutation.
        """
        if allocated_seq is None:
            seq_list = await cls.allocate_sequences(db, user_id, 1)
            allocated_seq = seq_list[0]

        event = UserSyncChangeFeed(
            id=str(uuid.uuid4()),
            user_id=user_id,
            change_seq=allocated_seq,
            entity_type=entity_type,
            entity_id=entity_id,
            operation=operation,
            payload=payload,
            created_at=datetime.now(timezone.utc)
        )
        db.add(event)
        await db.flush()
        return event

    @classmethod
    async def record_tombstone(
        cls,
        db: AsyncSession,
        user_id: str,
        entity_type: str,
        entity_id: str
    ) -> Tuple[UserSyncTombstone, UserSyncChangeFeed]:
        """
        Records a deletion event in both user_sync_tombstones and user_sync_change_feed.
        Supports repeated Create -> Delete -> Restore -> Delete lifecycles.
        """
        seq_list = await cls.allocate_sequences(db, user_id, 1)
        seq = seq_list[0]

        now = datetime.now(timezone.utc)
        tombstone = UserSyncTombstone(
            id=str(uuid.uuid4()),
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            change_seq=seq,
            deleted_at=now
        )
        db.add(tombstone)

        feed_event = UserSyncChangeFeed(
            id=str(uuid.uuid4()),
            user_id=user_id,
            change_seq=seq,
            entity_type=entity_type,
            entity_id=entity_id,
            operation="DELETE",
            payload={"entity_type": entity_type, "entity_id": entity_id, "deleted_at": now.isoformat()},
            created_at=now
        )
        db.add(feed_event)
        await db.flush()
        return tombstone, feed_event

    @classmethod
    async def pull_deltas(
        cls,
        db: AsyncSession,
        user_id: str,
        device_id: str,
        since_seq: int,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Retrieves committed deltas strictly ordered by change_seq ASC.
        Enforces 90-day retention boundary validation.
        """
        counter = await cls.get_or_create_counter(db, user_id)

        # 1. Retention Boundary Validation:
        # A cursor of min_available_seq - 1 is the boundary of valid retrievable changes.
        # If since_seq < min_available_seq - 1, the client has missed purged sequences.
        if since_seq < counter.min_available_seq - 1:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail={
                    "error": "SYNC_CURSOR_EXPIRED",
                    "action": "FULL_RESYNC_REQUIRED",
                    "min_available_seq": counter.min_available_seq,
                    "current_val": counter.current_val,
                    "message": "Client synchronization cursor is older than the retention boundary."
                }
            )

        # 2. Fetch change feed deltas
        stmt = (
            select(UserSyncChangeFeed)
            .where(
                UserSyncChangeFeed.user_id == user_id,
                UserSyncChangeFeed.change_seq > since_seq
            )
            .order_by(UserSyncChangeFeed.change_seq.asc())
            .limit(limit + 1)
        )
        feed_records = (await db.execute(stmt)).scalars().all()

        has_more = len(feed_records) > limit
        deltas = feed_records[:limit]

        # 3. Fetch matching tombstones in range
        tombstone_stmt = (
            select(UserSyncTombstone)
            .where(
                UserSyncTombstone.user_id == user_id,
                UserSyncTombstone.change_seq > since_seq
            )
            .order_by(UserSyncTombstone.change_seq.asc())
            .limit(limit)
        )
        tombstones = (await db.execute(tombstone_stmt)).scalars().all()

        max_seq = since_seq
        if deltas:
            max_seq = deltas[-1].change_seq

        # 4. Update device watermark tracking (last_synced_at timestamp only; does not prematurely ack unpersisted items)
        wm_stmt = select(UserSyncWatermark).where(
            UserSyncWatermark.user_id == user_id,
            UserSyncWatermark.device_id == device_id
        )
        wm = (await db.execute(wm_stmt)).scalar_one_or_none()
        if wm:
            wm.last_synced_at = datetime.now(timezone.utc)
            # update last_acknowledged_seq only up to max safely delivered sequence
            if max_seq > wm.last_acknowledged_seq:
                wm.last_acknowledged_seq = max_seq
        else:
            wm = UserSyncWatermark(
                user_id=user_id,
                device_id=device_id,
                last_acknowledged_seq=max_seq,
                last_synced_at=datetime.now(timezone.utc),
                client_app_version="1.0.0"
            )
            db.add(wm)
        await db.flush()

        return {
            "server_seq": max_seq,
            "has_more": has_more,
            "deltas": [
                {
                    "change_seq": d.change_seq,
                    "entity_type": d.entity_type,
                    "entity_id": d.entity_id,
                    "operation": d.operation,
                    "payload": d.payload,
                    "created_at": d.created_at
                }
                for d in deltas
            ],
            "tombstones": [
                {
                    "entity_type": t.entity_type,
                    "entity_id": t.entity_id,
                    "change_seq": t.change_seq,
                    "deleted_at": t.deleted_at.isoformat()
                }
                for t in tombstones
            ]
        }

    @classmethod
    async def cleanup_retention_window(
        cls,
        db: AsyncSession,
        user_id: str,
        retention_days: int = 90
    ) -> Dict[str, Any]:
        """
        Idempotent cleanup daemon for a user.
        Deletes feed rows and tombstones older than retention_days, advancing min_available_seq.
        """
        lock_stmt = select(UserSyncCounter).where(UserSyncCounter.user_id == user_id).with_for_update()
        counter = (await db.execute(lock_stmt)).scalar_one_or_none()
        if not counter:
            return {"purged_feed": 0, "purged_tombstones": 0}

        cutoff_date = datetime.now(timezone.utc).timestamp() - (retention_days * 86400)
        cutoff_dt = datetime.fromtimestamp(cutoff_date, tz=timezone.utc)

        # Find min change_seq committed at or after cutoff
        min_seq_stmt = select(UserSyncChangeFeed.change_seq).where(
            UserSyncChangeFeed.user_id == user_id,
            UserSyncChangeFeed.created_at >= cutoff_dt
        ).order_by(UserSyncChangeFeed.change_seq.asc()).limit(1)

        retained_min_seq = (await db.execute(min_seq_stmt)).scalar_one_or_none()
        if retained_min_seq is None:
            # If all are old or none exist, min_available_seq advances to current_val + 1
            retained_min_seq = counter.current_val + 1

        counter.min_available_seq = retained_min_seq
        counter.updated_at = datetime.now(timezone.utc)

        # Purge older feed items
        del_feed_stmt = delete(UserSyncChangeFeed).where(
            UserSyncChangeFeed.user_id == user_id,
            UserSyncChangeFeed.change_seq < retained_min_seq
        )
        feed_res = await db.execute(del_feed_stmt)

        # Purge older tombstones
        del_tomb_stmt = delete(UserSyncTombstone).where(
            UserSyncTombstone.user_id == user_id,
            UserSyncTombstone.change_seq < retained_min_seq
        )
        tomb_res = await db.execute(del_tomb_stmt)
        await db.flush()

        return {
            "purged_feed": feed_res.rowcount,
            "purged_tombstones": tomb_res.rowcount,
            "min_available_seq": retained_min_seq
        }
