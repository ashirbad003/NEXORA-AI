import asyncio
import json
import uuid
from typing import Dict, Set, Any, Optional
from fastapi import WebSocket
import asyncpg
from backend.app.core.config import settings
from backend.app.core.logging import logger

CHANNEL_NAME = "nexora_event_bus"

class NotificationConnectionManager:
    """
    WebSocket Connection Manager for Real-Time Event Dispatch (FEAT-308 & FEAT-290).
    Maintains active connections mapped by user_id and study rooms mapped by group_id.
    Includes distributed multi-worker event dispatch using PostgreSQL LISTEN/NOTIFY.
    """

    def __init__(self):
        # Unique instance id to avoid echoing local NOTIFY events back to ourselves
        self.instance_id = uuid.uuid4().hex[:12]
        # user_id -> Set[WebSocket]
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # group_id -> Set[WebSocket] (Virtual Pomodoro Room sync)
        self.room_connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()
        self._listener_conn: Optional[asyncpg.Connection] = None
        self._is_running = False

    def _get_pg_dsn(self) -> str:
        url = settings.DATABASE_URL
        if "postgresql+asyncpg://" in url:
            return url.replace("postgresql+asyncpg://", "postgresql://")
        return url

    async def start_listener(self):
        """Starts the PostgreSQL LISTEN background listener for multi-worker support."""
        if self._is_running:
            return

        dsn = self._get_pg_dsn()
        if not dsn.startswith("postgresql://"):
            logger.info("Non-PostgreSQL database configured; skipping LISTEN/NOTIFY listener.")
            return

        self._is_running = True
        try:
            self._listener_conn = await asyncpg.connect(dsn)
            await self._listener_conn.add_listener(CHANNEL_NAME, self._handle_pg_notification)
            logger.info(f"PostgreSQL event bus listener initialized on channel '{CHANNEL_NAME}' (instance {self.instance_id})")
        except Exception as e:
            logger.warning(f"Could not connect PostgreSQL LISTEN listener: {str(e)}. Operating in local-only mode.")

    async def stop_listener(self):
        """Stops the PostgreSQL LISTEN listener cleanly."""
        self._is_running = False
        if self._listener_conn:
            try:
                await self._listener_conn.remove_listener(CHANNEL_NAME, self._handle_pg_notification)
                await self._listener_conn.close()
                logger.info("PostgreSQL event bus listener disconnected cleanly.")
            except Exception as e:
                logger.warning(f"Error disconnecting PG listener: {str(e)}")
            finally:
                self._listener_conn = None

    def _handle_pg_notification(self, connection, pid, channel, payload):
        """Callback for incoming PostgreSQL NOTIFY payloads from other workers."""
        try:
            data = json.loads(payload)
            sender_instance = data.get("sender")
            if sender_instance == self.instance_id:
                # Ignore self-broadcast since local sockets were already notified
                return

            target = data.get("target")
            event_type = data.get("event")
            event_data = data.get("data")

            # Route in background task without blocking the asyncpg listener
            asyncio.create_task(self._dispatch_remote_event(target, event_type, event_data))
        except Exception as e:
            logger.error(f"Error processing PG NOTIFY payload: {str(e)}")

    async def _dispatch_remote_event(self, target: Dict[str, Any], event_type: str, data: Any):
        """Dispatches an event received from PostgreSQL NOTIFY to local connections."""
        target_type = target.get("type")
        if target_type == "user":
            user_id = target.get("id")
            await self._send_to_local_user(user_id, event_type, data)
        elif target_type == "room":
            room_id = target.get("id")
            await self._send_to_local_room(room_id, event_type, data)
        elif target_type == "broadcast":
            await self._broadcast_to_local(event_type, data)

    async def _publish_event(self, target: Dict[str, Any], event_type: str, data: Any):
        """Publishes an event to PostgreSQL NOTIFY channel for other workers to receive."""
        dsn = self._get_pg_dsn()
        if not dsn.startswith("postgresql://"):
            return

        payload = json.dumps({
            "sender": self.instance_id,
            "target": target,
            "event": event_type,
            "data": data
        })

        try:
            conn = await asyncpg.connect(dsn)
            try:
                await conn.execute("SELECT pg_notify($1, $2)", CHANNEL_NAME, payload)
            finally:
                await conn.close()
        except Exception as e:
            logger.warning(f"Failed to publish PG NOTIFY event: {str(e)}")

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = set()
            self.active_connections[user_id].add(websocket)
        logger.info(f"WebSocket connected for user {user_id}. Total active: {len(self.active_connections[user_id])}")

    async def disconnect(self, user_id: str, websocket: WebSocket):
        async with self._lock:
            if user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]

            for group_id, room_sockets in list(self.room_connections.items()):
                room_sockets.discard(websocket)
                if not room_sockets:
                    del self.room_connections[group_id]

        logger.info(f"WebSocket disconnected for user {user_id}")

    # --- FEAT-290: Virtual Pomodoro Room Synchronization ---
    async def join_pomodoro_room(self, group_id: str, websocket: WebSocket):
        async with self._lock:
            if group_id not in self.room_connections:
                self.room_connections[group_id] = set()
            self.room_connections[group_id].add(websocket)
        logger.info(f"WebSocket joined Pomodoro Room {group_id}. Total participants: {len(self.room_connections[group_id])}")

    async def broadcast_to_room(self, group_id: str, event_type: str, data: Any):
        # 1. Send to local sockets
        await self._send_to_local_room(group_id, event_type, data)
        # 2. Publish to other workers via PostgreSQL NOTIFY
        await self._publish_event({"type": "room", "id": group_id}, event_type, data)

    async def _send_to_local_room(self, group_id: str, event_type: str, data: Any):
        payload = {
            "event": event_type,
            "room_id": group_id,
            "data": data
        }
        async with self._lock:
            sockets = list(self.room_connections.get(group_id, []))

        for ws in sockets:
            try:
                await ws.send_json(payload)
            except Exception:
                pass

    # --- FEAT-308: User-Specific Event Delivery ---
    async def send_to_user(self, user_id: str, event_type: str, data: Any):
        # 1. Send to local sockets
        await self._send_to_local_user(user_id, event_type, data)
        # 2. Publish to other workers via PostgreSQL NOTIFY
        await self._publish_event({"type": "user", "id": user_id}, event_type, data)

    async def _send_to_local_user(self, user_id: str, event_type: str, data: Any):
        payload = {
            "event": event_type,
            "data": data
        }
        async with self._lock:
            sockets = list(self.active_connections.get(user_id, []))

        for ws in sockets:
            try:
                await ws.send_json(payload)
            except Exception as e:
                logger.warning(f"Failed to send WS message to user {user_id}: {str(e)}")
                await self.disconnect(user_id, ws)

    async def broadcast_event(self, event_type: str, data: Any):
        # 1. Send to local sockets
        await self._broadcast_to_local(event_type, data)
        # 2. Publish to other workers via PostgreSQL NOTIFY
        await self._publish_event({"type": "broadcast"}, event_type, data)

    async def _broadcast_to_local(self, event_type: str, data: Any):
        payload = {
            "event": event_type,
            "data": data
        }
        async with self._lock:
            all_sockets = [ws for sockets in self.active_connections.values() for ws in sockets]

        for ws in all_sockets:
            try:
                await ws.send_json(payload)
            except Exception:
                pass

ws_manager = NotificationConnectionManager()
