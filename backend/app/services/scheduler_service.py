import asyncio
import uuid
import zoneinfo
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy import select, and_, func, or_

from backend.app.db.session import AsyncSessionLocal
from backend.app.models.phase10_notifications import UserNotification, UserNotificationPreference
from backend.app.models.phase10_revision import StudentCardReview, FlashcardItem
from backend.app.models.phase10_peer import PeerDiscussionThread, PeerDiscussionReply
from backend.app.models.phase9_portals import PlacementDrive, PlacementDriveRegistration
from backend.app.models.auth import User, StudentProfile
from backend.app.services.notification_service import NotificationService
from backend.app.schemas.phase10_notifications import NotificationCreateInternal
from backend.app.core.logging import logger

class NotificationScheduler:
    """
    FastAPI Lifespan-Managed Recurring Task Scheduler.
    Executes background cycles for:
      1. FEAT-303: Daily Revision Due Reminder
      2. FEAT-292: Weekly Peer Collaboration Digest
      3. FEAT-306: Placement Drive Deadline Alert
    Ensures safe, idempotent notifications, timezone conversion, quiet-hours suppression,
    and PostgreSQL advisory lock coordination for multi-process environments.
    """

    ADVISORY_LOCK_ID = 9182736450123984  # Unique 64-bit int for PostgreSQL advisory locking

    def __init__(self, check_interval_seconds: int = 60):
        self.check_interval_seconds = check_interval_seconds
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        if self.is_running:
            return
        self.is_running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("NotificationScheduler background worker started.")

    async def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("NotificationScheduler background worker stopped cleanly.")

    async def _run_loop(self):
        while self.is_running:
            try:
                await self.run_scheduled_tasks()
            except Exception as e:
                logger.error(f"Error in NotificationScheduler cycle: {str(e)}", exc_info=True)
            await asyncio.sleep(self.check_interval_seconds)

    async def run_scheduled_tasks(self):
        """
        Executes all periodic jobs guarded by PostgreSQL advisory locking
        to prevent race conditions in multi-worker environments.
        """
        async with AsyncSessionLocal() as db:
            # Try to acquire PostgreSQL session advisory lock (non-blocking)
            try:
                lock_res = await db.execute(func.pg_try_advisory_lock(self.ADVISORY_LOCK_ID))
                has_lock = lock_res.scalar()
                if not has_lock:
                    logger.debug("Another worker holds the scheduler advisory lock. Skipping this cycle.")
                    return
            except Exception as e:
                # If non-PostgreSQL dialect (e.g. SQLite tests), proceed directly
                has_lock = True

            try:
                await self.process_daily_revision_reminders(db)
                await self.process_weekly_peer_digests(db)
                await self.process_placement_deadline_alerts(db)
            finally:
                if has_lock:
                    try:
                        await db.execute(func.pg_advisory_unlock(self.ADVISORY_LOCK_ID))
                    except Exception:
                        pass

    # --- FEAT-303: Daily Revision Due Reminder ---
    async def process_daily_revision_reminders(self, db):
        now_utc = datetime.now(timezone.utc)
        # Find users who have cards due right now
        due_query = select(StudentCardReview.user_id, func.count(StudentCardReview.id).label("due_count")).where(
            StudentCardReview.next_review_at <= now_utc
        ).group_by(StudentCardReview.user_id)
        
        results = (await db.execute(due_query)).all()
        for user_id, due_count in results:
            if due_count == 0:
                continue

            # Fetch user profile to check timezone and preferences
            user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
            if not user or not user.is_active:
                continue

            # Resolve timezone
            profile = (await db.execute(select(StudentProfile).where(StudentProfile.user_id == user_id))).scalar_one_or_none()
            tz_str = profile.timezone if profile and profile.timezone else "UTC"
            try:
                user_tz = zoneinfo.ZoneInfo(tz_str)
            except Exception:
                user_tz = timezone.utc

            now_local = now_utc.astimezone(user_tz)
            today_str = now_local.strftime("%Y-%m-%d")

            # Check quiet hours & preference
            pref = await NotificationService.get_or_create_preferences(db, user_id)
            if not pref.in_app_enabled:
                continue

            if pref.quiet_hours_start and pref.quiet_hours_end:
                curr_time_str = now_local.strftime("%H:%M")
                if pref.quiet_hours_start <= curr_time_str <= pref.quiet_hours_end:
                    continue

            # Idempotency check: has reminder already been sent today?
            existing_today = (await db.execute(
                select(UserNotification).where(
                    UserNotification.user_id == user_id,
                    UserNotification.category == "REVISION",
                    UserNotification.payload["schedule_tag"].astext == f"daily_due_{today_str}"
                )
            )).scalar_one_or_none()

            if existing_today:
                continue

            # Dispatch notification
            await NotificationService.send_notification(
                db,
                NotificationCreateInternal(
                    user_id=user_id,
                    category="REVISION",
                    urgency="NORMAL",
                    title="Flashcards Ready for Review",
                    message=f"You have {due_count} flashcard(s) due today. Keep your memory retention peak!",
                    action_url="/revision",
                    payload={"schedule_tag": f"daily_due_{today_str}", "due_count": due_count}
                )
            )

    # --- FEAT-292: Weekly Peer Collaboration Digest ---
    async def process_weekly_peer_digests(self, db):
        now_utc = datetime.now(timezone.utc)
        # Run on Sundays or weekly window (ISO week)
        iso_year, iso_week, iso_day = now_utc.isocalendar()
        week_tag = f"weekly_digest_{iso_year}_{iso_week}"

        users = (await db.execute(select(User).where(User.is_active == True))).scalars().all()
        one_week_ago = now_utc - timedelta(days=7)

        # Count new threads in the past week
        new_threads_count = (await db.execute(
            select(func.count(PeerDiscussionThread.id)).where(PeerDiscussionThread.created_at >= one_week_ago)
        )).scalar() or 0

        if new_threads_count == 0:
            return  # Suppress empty digest

        for user in users:
            pref = await NotificationService.get_or_create_preferences(db, user.id)
            if not pref.in_app_enabled:
                continue

            existing = (await db.execute(
                select(UserNotification).where(
                    UserNotification.user_id == user.id,
                    UserNotification.category == "COMMUNITY",
                    UserNotification.payload["schedule_tag"].astext == week_tag
                )
            )).scalar_one_or_none()

            if existing:
                continue

            await NotificationService.send_notification(
                db,
                NotificationCreateInternal(
                    user_id=user.id,
                    category="COMMUNITY",
                    urgency="LOW",
                    title=f"Weekly Peer Learning Digest (Week {iso_week})",
                    message=f"{new_threads_count} new peer discussion thread(s) opened this week. Check out what your peers are solving!",
                    action_url="/community",
                    payload={"schedule_tag": week_tag, "new_threads_count": new_threads_count}
                )
            )

    # --- FEAT-306: Placement Drive Deadline Alert ---
    async def process_placement_deadline_alerts(self, db):
        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
        alert_window = now_naive + timedelta(hours=24)

        # Find placement drives closing registration in the next 24 hours
        drives = (await db.execute(
            select(PlacementDrive).where(
                PlacementDrive.registration_deadline.is_not(None),
                PlacementDrive.registration_deadline > now_naive,
                PlacementDrive.registration_deadline <= alert_window,
                PlacementDrive.status != "Completed"
            )
        )).scalars().all()

        for drive in drives:
            # Find eligible students not yet registered
            users = (await db.execute(select(User).where(User.is_active == True))).scalars().all()
            for user in users:
                # Check if already registered
                reg = (await db.execute(
                    select(PlacementDriveRegistration).where(
                        PlacementDriveRegistration.drive_id == drive.id,
                        PlacementDriveRegistration.student_id == user.id
                    )
                )).scalar_one_or_none()
                if reg:
                    continue

                schedule_tag = f"drive_deadline_{drive.id}"
                existing_alert = (await db.execute(
                    select(UserNotification).where(
                        UserNotification.user_id == user.id,
                        UserNotification.category == "PLACEMENT",
                        UserNotification.payload["schedule_tag"].astext == schedule_tag
                    )
                )).scalar_one_or_none()

                if existing_alert:
                    continue

                await NotificationService.send_notification(
                    db,
                    NotificationCreateInternal(
                        user_id=user.id,
                        category="PLACEMENT",
                        urgency="HIGH",
                        title=f"Deadline Alert: {drive.company_name} ({drive.role_title})",
                        message=f"Registration for {drive.company_name} closes in less than 24 hours. Submit your registration now!",
                        action_url="/placement",
                        payload={"schedule_tag": schedule_tag, "drive_id": drive.id}
                    )
                )

scheduler = NotificationScheduler(check_interval_seconds=60)
