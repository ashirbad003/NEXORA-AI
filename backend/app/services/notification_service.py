import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, desc, and_
from fastapi import HTTPException

from backend.app.models.phase10_notifications import (
    UserNotification, UserNotificationPreference
)
from backend.app.schemas.phase10_notifications import (
    NotificationCreateInternal, NotificationPreferencesUpdate
)
from backend.app.services.websocket_manager import ws_manager
from backend.app.core.logging import logger

class NotificationService:

    @classmethod
    async def get_or_create_preferences(cls, db: AsyncSession, user_id: str) -> UserNotificationPreference:
        pref = (await db.execute(select(UserNotificationPreference).where(UserNotificationPreference.user_id == user_id))).scalar_one_or_none()
        if not pref:
            pref = UserNotificationPreference(
                user_id=user_id,
                in_app_enabled=True,
                email_enabled=True,
                push_enabled=False,
                category_overrides={}
            )
            db.add(pref)
            await db.commit()
            await db.refresh(pref)
        return pref

    @classmethod
    async def update_preferences(cls, db: AsyncSession, user_id: str, data: NotificationPreferencesUpdate) -> UserNotificationPreference:
        pref = await cls.get_or_create_preferences(db, user_id)
        if data.in_app_enabled is not None:
            pref.in_app_enabled = data.in_app_enabled
        if data.email_enabled is not None:
            pref.email_enabled = data.email_enabled
        if data.push_enabled is not None:
            pref.push_enabled = data.push_enabled
        if data.category_overrides is not None:
            pref.category_overrides = data.category_overrides
        if data.quiet_hours_start is not None:
            pref.quiet_hours_start = data.quiet_hours_start
        if data.quiet_hours_end is not None:
            pref.quiet_hours_end = data.quiet_hours_end

        await db.commit()
        await db.refresh(pref)
        return pref

    @classmethod
    async def send_notification(cls, db: AsyncSession, data: NotificationCreateInternal) -> UserNotification:
        pref = await cls.get_or_create_preferences(db, data.user_id)
        
        # Check if in-app notifications are enabled
        if not pref.in_app_enabled:
            logger.info(f"In-app notifications disabled for user {data.user_id}. Skipping.")
            return None

        # Check category override
        if data.category in pref.category_overrides:
            cat_cfg = pref.category_overrides.get(data.category, {})
            if cat_cfg.get("enabled") is False:
                logger.info(f"Notification category {data.category} disabled for user {data.user_id}.")
                return None

        notification = UserNotification(
            user_id=data.user_id,
            category=data.category,
            urgency=data.urgency,
            title=data.title,
            message=data.message,
            action_url=data.action_url,
            payload=data.payload or {},
            is_read=False
        )
        db.add(notification)
        await db.commit()
        await db.refresh(notification)

        # Dispatch real-time WebSocket push (FEAT-308)
        unread_count = (await db.execute(
            select(func.count(UserNotification.id)).where(
                UserNotification.user_id == data.user_id,
                UserNotification.is_read == False
            )
        )).scalar() or 0

        await ws_manager.send_to_user(
            user_id=data.user_id,
            event_type="NOTIFICATION_NEW",
            data={
                "id": notification.id,
                "category": notification.category,
                "urgency": notification.urgency,
                "title": notification.title,
                "message": notification.message,
                "action_url": notification.action_url,
                "created_at": notification.created_at.isoformat(),
                "unread_count": unread_count
            }
        )

        return notification

    @classmethod
    async def list_notifications(cls, db: AsyncSession, user_id: str, unread_only: bool = False, limit: int = 50) -> List[UserNotification]:
        query = select(UserNotification).where(UserNotification.user_id == user_id)
        if unread_only:
            query = query.where(UserNotification.is_read == False)
        query = query.order_by(desc(UserNotification.created_at)).limit(limit)
        return (await db.execute(query)).scalars().all()

    @classmethod
    async def mark_as_read(cls, db: AsyncSession, user_id: str, notification_id: str) -> bool:
        stmt = update(UserNotification).where(
            UserNotification.id == notification_id,
            UserNotification.user_id == user_id
        ).values(is_read=True, read_at=datetime.now(timezone.utc))
        res = await db.execute(stmt)
        await db.commit()
        return res.rowcount > 0

    @classmethod
    async def mark_all_as_read(cls, db: AsyncSession, user_id: str) -> int:
        stmt = update(UserNotification).where(
            UserNotification.user_id == user_id,
            UserNotification.is_read == False
        ).values(is_read=True, read_at=datetime.now(timezone.utc))
        res = await db.execute(stmt)
        await db.commit()
        return res.rowcount

    @classmethod
    async def get_unread_count(cls, db: AsyncSession, user_id: str) -> int:
        stmt = select(func.count(UserNotification.id)).where(
            UserNotification.user_id == user_id,
            UserNotification.is_read == False
        )
        return (await db.execute(stmt)).scalar() or 0
