"""Sync endpoints — trigger ingestion and check status."""

import asyncio
import logging
import sqlite3

from fastapi import APIRouter
from pydantic import BaseModel

from core.config import settings
from core.credentials import get_credentials
from core.db import get_db
from core.scheduler import reschedule_sync
from services.adzuna_client import AdzunaClient, RateLimitError
from services.sync_orchestrator import run_sync

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["sync"])


class SchedulePayload(BaseModel):
    hour: int
    minute: int


class ScheduleResponse(BaseModel):
    hour: int
    minute: int


class TestConnectionResponse(BaseModel):
    connected: bool
    jobs_available: int = 0
    error: str | None = None


class SyncTriggerResponse(BaseModel):
    status: str


class SyncStatusResponse(BaseModel):
    status: str
    last_sync: str | None = None
    jobs_fetched: int = 0
    jobs_inserted: int = 0
    jobs_skipped: int = 0
    error_message: str | None = None


@router.post("/sync/trigger", status_code=202, response_model=SyncTriggerResponse)
async def trigger_sync() -> SyncTriggerResponse:
    """Kick off a background sync job. Returns immediately."""
    db = get_db()
    asyncio.create_task(_run_sync_background(db))
    return SyncTriggerResponse(status="started")


async def _run_sync_background(db: sqlite3.Connection) -> None:
    """Wrapper to run sync and catch any unhandled exceptions."""
    try:
        await run_sync(db)
    except Exception as e:
        logger.error("Background sync failed: %s", e)


@router.get("/sync/status", response_model=SyncStatusResponse)
async def sync_status() -> SyncStatusResponse:
    """Return the most recent sync log entry."""
    db = get_db()
    row = db.execute(
        """
        SELECT status, completed_at, jobs_fetched, jobs_inserted,
               jobs_skipped, error_message
        FROM sync_log
        ORDER BY id DESC
        LIMIT 1
        """
    ).fetchone()

    if row is None:
        return SyncStatusResponse(status="idle")

    return SyncStatusResponse(
        status=row["status"],
        last_sync=row["completed_at"],
        jobs_fetched=row["jobs_fetched"],
        jobs_inserted=row["jobs_inserted"],
        jobs_skipped=row["jobs_skipped"],
        error_message=row["error_message"],
    )


@router.get("/sync/schedule", response_model=ScheduleResponse)
async def get_schedule() -> ScheduleResponse:
    """Return the current sync schedule."""
    return ScheduleResponse(hour=settings.sync_hour, minute=settings.sync_minute)


@router.post("/sync/schedule", response_model=ScheduleResponse)
async def set_schedule(payload: SchedulePayload) -> ScheduleResponse:
    """Update the sync schedule."""
    settings.sync_hour = payload.hour
    settings.sync_minute = payload.minute
    reschedule_sync(payload.hour, payload.minute)
    return ScheduleResponse(hour=payload.hour, minute=payload.minute)


@router.get("/sync/test", response_model=TestConnectionResponse)
async def test_connection() -> TestConnectionResponse:
    """Test Adzuna API connection with current credentials."""
    creds = get_credentials()
    if creds is None:
        return TestConnectionResponse(connected=False, error="No credentials configured")

    try:
        client = AdzunaClient(creds[0], creds[1], settings.adzuna_country)
        jobs = await client.fetch_jobs("software engineer", "", page=1, results_per_page=1)
        return TestConnectionResponse(connected=True, jobs_available=len(jobs))
    except RateLimitError:
        return TestConnectionResponse(connected=False, error="Rate limited — try again later")
    except Exception as e:
        return TestConnectionResponse(connected=False, error=str(e))
