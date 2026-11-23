import unittest
import uuid
from typing import Tuple, List, Dict, Any, Optional
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.main import create_app
from backend.app.models.auth import User, Role
from backend.app.models.phase10_revision import (
    FlashcardDeck, FlashcardItem, StudentCardReview, StudentCardReviewLog
)
from backend.app.models.phase11_sync import (
    MobileDeviceToken, UserSyncCounter, UserSyncWatermark, UserSyncChangeFeed, UserSyncTombstone
)
from backend.app.services.auth_service import AuthService
from backend.app.services.sync_service import SyncService
from backend.app.core.config import settings
class TestPhase11MobileSyncInfrastructure(unittest.IsolatedAsyncioTestCase):

    async def _create_test_student(self, session: AsyncSession, email_prefix: str = "p11_student") -> Tuple[User, str]:
        from backend.app.schemas.user import StudentRegisterRequest, LoginRequest
        unique_id = str(uuid.uuid4())[0:8]
        email = f"{email_prefix}_{unique_id}@nexora.ai"
        password = "StrongPassword123!"
        req = StudentRegisterRequest(
            email=email,
            password=password,
            full_name="Phase 11 Sync Tester"
        )
        user = await AuthService.register_student(session=session, req=req)
        await session.commit()

        login_req = LoginRequest(email=email, password=password)
        auth_user, access_token, _ = await AuthService.authenticate_user(session=session, req=login_req)
        await session.commit()
        return auth_user, access_token

    async def _create_test_deck_and_card(self, session: AsyncSession, user_id: str) -> Tuple[str, str]:
        deck = FlashcardDeck(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title="Algorithm Basics",
            category="DSA",
            is_public=False
        )
        session.add(deck)
        await session.flush()

        card = FlashcardItem(
            id=str(uuid.uuid4()),
            deck_id=deck.id,
            prompt="What is binary search time complexity?",
            answer="Oblog N)",
            order_index=1
        )
        session.add(card)
        await session.flush()
        return deck.id, card.id

    async def test_01_device_token_registration_and_rotation(self):
        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            from backend.app.db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                user1, token1 = await self._create_test_student(session, "p11_dev1")
                user2, token2 = await self._create_test_student(session, "p11_dev2")

            headers1 = {"Authorization": f"Bearer {token1}"}
            headers2 = {"Authorization": f"Bearer {token2}"}

            payload1 = {
                "device_id": "mob_pixel_001",
                "expo_push_token": "ExponentPushToken[user1_token_aaa]",
                "device_os": "ANDROID",
                "device_model": "Pixel 8 Pro",
                "app_version": "1.0.0"
            }
            res1 = await client.post("/api/v1/notifications/devices/register", json=payload1, headers=headers1)
            assert res1.status_code == 200, res1.text
            data1 = res1.json()
            assert data1["device_id"] == "mob_pixel_001"
            assert data1["is_active"] is True

            payload1_rotated = {
                "device_id": "mob_pixel_001",
                "expo_push_token": "ExponentPushToken[user1_token_bbb]",
                "device_os": "ANDROID",
                "device_model": "Pixel 8 Pro",
                "app_version": "1.0.1"
            }
            res1_rot = await client.post("/api/v1/notifications/devices/register", json=payload1_rotated, headers=headers1)
            assert res1_rot.status_code == 200
            assert res1_rot.json()["expo_push_token"] == "ExponentPushToken[user1_token_bbb]"

            payload2_reassign = {
                "device_id": "mob_samsung_002",
                "expo_push_token": "ExponentPushToken[user1_token_bbb]",
                "device_os": "ANDROID",
                "device_model": "Pixel 8 Pro",
                "app_version": "1.0.1"
            }
            res2 = await client.post("/api/v1/notifications/devices/register", json=payload2_reassign, headers=headers2)
            assert res2.status_code == 200

            async with AsyncSessionLocal() as session:
                u1_tok = (await session.execute(
                    select(MobileDeviceToken).where(
                        MobileDeviceToken.user_id == user1.id,
                        MobileDeviceToken.device_id == "mob_pixel_001"
                    )
                )).scalar_one()
                assert u1_tok.is_active is False

    async def test_02_global_sequence_allocation_and_concurrency(self):
        from backend.app.db.session import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            user, _ = await self._create_test_student(session, "p11_seq")
            seqs1 = await SyncService.allocate_sequences(session, user.id, count=3)
            seqs2 = await SyncService.allocate_sequences(session, user.id, count=2)
            await session.commit()

        assert seqs1 == [1, 2, 3]
        assert seqs2 == [4, 5]

    async def test_03_sm2_version_aware_server_ordering(self):
        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            from backend.app.db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                user, token = await self._create_test_student(session, "p11_sm2")
                deck_id, card_id = await self._create_test_deck_and_card(session, user.id)
                await session.commit()

            headers = {"Authorization": f"Bearer {token}"}

            op1_id = f"op_review_{uuid.uuid4().hex}"
            res1 = await client.post(
                "/api/v1/sync/push",
                json={
                    "device_id": "mob_test_dev",
                    "operations": [
                        {
                            "op_id": op1_id,
                            "action_type": "SUBMIT_CARD_REVIEW",
                            "client_timestamp": datetime.now(timezone.utc).isoformat(),
                            "payload": {
                                "card_id": card_id,
                                "grade": 5,
                                "base_state_version": 1
                            }
                        }
                    ]
                },
                headers=headers
            )
            assert res1.status_code == 200, res1.text
            data1 = res1.json()["results"][0]
            assert data1["status"] == "SUCCESS", f"data1 was {data1}"
            assert data1["is_superseded"] is False
            assert data1["resulting_state_version"] == 2
            assert data1["repetition"] == 1

            res1_replay = await client.post(
                "/api/v1/sync/push",
                json={
                    "device_id": "mob_test_dev",
                    "operations": [
                        {
                            "op_id": op1_id,
                            "action_type": "SUBMIT_CARD_REVIEW",
                            "client_timestamp": datetime.now(timezone.utc).isoformat(),
                            "payload": {
                                "card_id": card_id,
                                "grade": 5,
                                "base_state_version": 1
                            }
                        }
                    ]
                },
                headers=headers
            )
            assert res1_replay.status_code == 200
            assert res1_replay.json()["results"][0]["is_replayed"] is True

            res_web = await client.post(
                "/api/v1/revision/reviews/submit",
                json={
                    "card_id": card_id,
                    "grade": 4,
                    "idempotency_key": f"web_rev_{uuid.uuid4().hex}",
                    "base_state_version": 2
                },
                headers=headers
            )
            assert res_web.status_code == 200
            assert res_web.json()["resulting_state_version"] == 3
            assert res_web.json()["repetition"] == 2

            op_stale_id = f"op_stale_{uuid.uuid4().hex}"
            res_stale = await client.post(
                "/api/v1/sync/push",
                json={
                    "device_id": "mob_test_dev",
                    "operations": [
                        {
                            "op_id": op_stale_id,
                            "action_type": "SUBMIT_CARD_REVIEW",
                            "client_timestamp": datetime.now(timezone.utc).isoformat(),
                            "payload": {
                                "card_id": card_id,
                                "grade": 2,
                                "base_state_version": 1
                            }
                        }
                    ]
                },
                headers=headers
            )
            assert res_stale.status_code == 200
            data_stale = res_stale.json()["results"][0]
            assert data_stale["status"] == "SUPERSEDED"
            assert data_stale["is_superseded"] is True
            assert data_stale["repetition"] == 2

            async with AsyncSessionLocal() as session:
                log_entry = (await session.execute(
                    select(StudentCardReviewLog).where(
                        StudentCardReviewLog.idempotency_key == op_stale_id
                    )
                )).scalar_one()
                assert log_entry.is_superseded is True
                assert log_entry.submitted_grade == 2

    async def test_04_sync_pull_delta_pagination_and_tombstones(self):
        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            from backend.app.db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                user, token = await self._create_test_student(session, "p11_pull")
                for i in range(3):
                    await SyncService.append_change_event(
                        db=session,
                        user_id=user.id,
                        entity_type="FLASHCARD_DECK",
                        entity_id=str(uuid.uuid4()),
                        operation="UPSERT",
                        payload={"deck_num": i}
                    )
                tomb, _ = await SyncService.record_tombstone(
                    db=session,
                    user_id=user.id,
                    entity_type="FLASHCARD_DECK",
                    entity_id="deleted_deck_xyz"
                )
                await session.commit()

            headers = {"Authorization": f"Bearer {token}"}

            res1 = await client.get("/api/v1/sync/pull?device_id=dev_p11_01&since_seq=0&limit=2", headers=headers)
            assert res1.status_code == 200, res1.text
            d1 = res1.json()
            assert len(d1["deltas"]) == 2
            assert d1["has_more"] is True
            page1_max = d1["server_seq"]
            assert page1_max == 2

            res2 = await client.get(f"/api/v1/sync/pull?device_id=dev_p11_01&since_seq={page1_max}&limit=5", headers=headers)
            assert res2.status_code == 200
            d2 = res2.json()
            assert len(d2["deltas"]) == 2
            assert d2["has_more"] is False
            assert len(d2["tombstones"]) == 1
            assert d2["tombstones"][0]["entity_id"] == "deleted_deck_xyz"

    async def test_04_sync_pull_delta_pagination_and_tombstones(self):
        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            from backend.app.db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as session:
                user, token = await self._create_test_student(session, "p11_pull")
                for i in range(3):
                    await SyncService.append_change_event(
                        db=session,
                        user_id=user.id,
                        entity_type="FLASHCARD_DECK",
                        entity_id=str(uuid.uuid4()),
                        operation="UPSERT",
                        payload={"deck_num": i}
                    )
                tomb, _ = await SyncService.record_tombstone(
                    db=session,
                    user_id=user.id,
                    entity_type="FLASHCARD_DECK",
                    entity_id="deleted_deck_xyz"
                )
                await session.commit()

            headers = {"Authorization": f"Bearer {token}"}

            res1 = await client.get("/api/v1/sync/pull?device_id=dev_p11_01&since_seq=0&limit=2", headers=headers)
            assert res1.status_code == 200, res1.text
            d1 = res1.json()
            assert len(d1["deltas"]) == 2
            assert d1["has_more"] is True
            page1_max = d1["server_seq"]
            assert page1_max == 2

            res2 = await client.get(f"/api/v1/sync/pull?device_id=dev_p11_01&since_seq={page1_max}&limit=5", headers=headers)
            assert res2.status_code == 200
            d2 = res2.json()
            assert len(d2["deltas"]) == 2
            assert d2["has_more"] is False
            assert len(d2["tombstones"]) == 1
            assert d2["tombstones"][0]["entity_id"] == "deleted_deck_xyz"

    async def test_05_retention_boundary_and_expired_cursor_full_resync(self):
        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            from backend.app.db.session import AsyncSessionLocal
            from backend.app.models.phase11_sync import UserSyncChangeFeed

            async with AsyncSessionLocal() as session:
                user, token = await self._create_test_student(session, "p11_retention")
                for i in range(5):
                    await SyncService.append_change_event(
                        db=session,
                        user_id=user.id,
                        entity_type="FLASHCARD_DECK",
                        entity_id=str(uuid.uuid4()),
                        operation="UPSERT",
                        payload={"num": i}
                    )
                await session.commit()

            headers = {"Authorization": f"Bearer {token}"}

            res_valid = await client.get("/api/v1/sync/pull?device_id=dev_p11_01&since_seq=2", headers=headers)
            assert res_valid.status_code == 200

            # Prune events and advance min_available_seq to simulate retention boundary
            async with AsyncSessionLocal() as session:
                from sqlalchemy import delete, update
                await session.execute(
                    delete(UserSyncChangeFeed).where(
                        UserSyncChangeFeed.user_id == user.id,
                        UserSyncChangeFeed.change_seq <= 3
                    )
                )
                from backend.app.models.phase11_sync import UserSyncCounter
                await session.execute(
                    update(UserSyncCounter).where(
                        UserSyncCounter.user_id == user.id
                    ).values(min_available_seq=4)
                )
                await session.commit()

            # Device requesting from since_seq=1 has fallen behind min_available_seq (4)
            # Expect HTTP 410 GONE requiring full resync
            res_expired = await client.get("/api/v1/sync/pull?device_id=dev_p11_01&since_seq=1", headers=headers)
            assert res_expired.status_code == 410
            err_data = res_expired.json()
            assert "detail" in err_data
            assert err_data["detail"]["error"] == "SYNC_CURSOR_EXPIRED"
            assert err_data["detail"]["action"] == "FULL_RESYNC_REQUIRED"

    async def test_06_sync_snapshot_and_cross_user_idor_defense(self):
        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            from backend.app.db.session import AsyncSessionLocal

            async with AsyncSessionLocal() as session:
                user_a, token_a = await self._create_test_student(session, "p11_user_a")
                user_b, token_b = await self._create_test_student(session, "p11_user_b")

                # User A has private deck
                deck_a = FlashcardDeck(
                    user_id=user_a.id,
                    title="User A Secret Deck",
                    description="Private to user A",
                    tags=["confidential"]
                )
                session.add(deck_a)
                await session.flush()
                item_a = FlashcardItem(
                    deck_id=deck_a.id,
                    prompt="Question A",
                    answer="Answer A"
                )
                session.add(item_a)
                await session.commit()

            headers_a = {"Authorization": f"Bearer {token_a}"}
            headers_b = {"Authorization": f"Bearer {token_b}"}

            # User A gets snapshot including deck
            snap_res_a = await client.get("/api/v1/sync/snapshot?device_id=dev_a_01", headers=headers_a)
            assert snap_res_a.status_code == 200
            snap_a = snap_res_a.json()
            assert len(snap_a["decks"]) == 1
            assert snap_a["decks"][0]["title"] == "User A Secret Deck"

            # User B snapshot contains 0 decks (strict user isolation)
            snap_res_b = await client.get("/api/v1/sync/snapshot?device_id=dev_b_01", headers=headers_b)
            assert snap_res_b.status_code == 200
            snap_b = snap_res_b.json()
            assert len(snap_b["decks"]) == 0

            # User B sync pull has 0 deltas
            pull_res_b = await client.get("/api/v1/sync/pull?device_id=dev_b_01&since_seq=0", headers=headers_b)
            assert pull_res_b.status_code == 200
            assert len(pull_res_b.json()["deltas"]) == 0
