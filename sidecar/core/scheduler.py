"""APScheduler configuration for nightly sync jobs."""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from core.config import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _run_scheduled_sync() -> None:
    """Run sync as a scheduled job. Handles missing credentials gracefully."""
    from core.credentials import get_credentials
    from core.db import get_db
    from services.sync_orchestrator import run_sync

    if get_credentials() is None:
        logger.warning("Scheduled sync skipped: no credentials configured")
        return

    logger.info("Starting scheduled sync")
    try:
        await run_sync(get_db())
    except Exception as e:
        logger.error("Scheduled sync failed: %s", e)


def setup_scheduler() -> None:
    """Configure and start the APScheduler with the nightly sync job."""
    scheduler.add_job(
        _run_scheduled_sync,
        CronTrigger(hour=settings.sync_hour, minute=settings.sync_minute),
        id="nightly_sync",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "Scheduler started: nightly sync at %02d:%02d",
        settings.sync_hour,
        settings.sync_minute,
    )


def reschedule_sync(hour: int, minute: int) -> None:
    """Reschedule the nightly sync job to a new time."""
    if scheduler.running:
        scheduler.reschedule_job(
            "nightly_sync",
            trigger=CronTrigger(hour=hour, minute=minute),
        )
        logger.info("Rescheduled sync to %02d:%02d", hour, minute)


def shutdown_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shut down")
