import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from backend.app.db.session import get_db_session, AsyncSessionLocal
from backend.app.api.deps import get_current_user
from backend.app.core.config import settings
from backend.app.models.auth import User
from backend.app.schemas.phase10_notifications import (
    NotificationResponse, NotificationPreferencesUpdate, NotificationPreferencesResponse
)
from backend.app.services.notification_service import NotificationService
from backend.app.services.websocket_manager import ws_manager
from backend.app.core.logging import logger

router = APIRouter(prefix="/notifications", tags=["Notifications & Real-Time Event Bus"])

@router.get("", response_model=List[NotificationResponse])
async def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    return await NotificationService.list_notifications(db, current_user.id, unread_only=unread_only, limit=limit)

@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    count = await NotificationService.get_unread_count(db, current_user.id)
    return {"unread_count": count}

@router.post("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    success = await NotificationService.mark_as_read(db, current_user.id, notification_id)
    return {"marked_read": success}

@router.post("/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    count = await NotificationService.mark_all_as_read(db, current_user.id)
    return {"marked_read_count": count}

@router.get("/preferences", response_model=NotificationPreferencesResponse)
async def get_notification_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    return await NotificationService.get_or_create_preferences(db, current_user.id)

@router.put("/preferences", response_model=NotificationPreferencesResponse)
async def update_notification_preferences(
    payload: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    return await NotificationService.update_preferences(db, current_user.id, payload)

# --- Real-Time WebSocket Event Bus (FEAT-308) ---

@router.websocket("/ws")
async def websocket_notifications_endpoint(websocket: WebSocket, token: Optional[str] = Query(None)):
    """
    Authenticated WebSocket endpoint for real-time notification push events.
    Verifies JWT token from query parameter.
    """
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
    except Exception as e:
        logger.warning(f"WebSocket auth failed: {str(e)}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await ws_manager.connect(user_id, websocket)

    # Send initial unread count
    try:
        async with AsyncSessionLocal() as db:
            unread_cnt = await NotificationService.get_unread_count(db, user_id)
        await websocket.send_json({
            "event": "INITIAL_STATE",
            "data": {"unread_count": unread_cnt}
        })

        while True:
            # Heartbeat listener
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        await ws_manager.disconnect(user_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {str(e)}")
        await ws_manager.disconnect(user_id, websocket)
