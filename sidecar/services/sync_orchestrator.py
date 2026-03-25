"""Sync orchestrator — fetches jobs from Adzuna, processes them, writes to SQLite."""

import asyncio
import logging
import sqlite3
from datetime import datetime, timezone

from core.config import settings
from core.credentials import get_credentials
from services.adzuna_client import AdzunaClient, AdzunaJob, RateLimitError
from services.nlp_pipeline import get_pipeline
from services.role_normalizer import RoleNormalizer
from services.salary_resolver import resolve_salary

logger = logging.getLogger(__name__)

SEARCH_QUERIES: list[tuple[str, str]] = [
    ("software engineer", ""),
    ("devops engineer", ""),
    ("data engineer", ""),
]


def _create_sync_log(db: sqlite3.Connection) -> int:
    """Create a sync_log entry with status 'running'. Returns the log ID."""
    cursor = db.execute(
        "INSERT INTO sync_log (status) VALUES ('running')"
    )
    db.commit()
    return cursor.lastrowid  # type: ignore[return-value]


def _update_sync_log(
    db: sqlite3.Connection,
    sync_id: int,
    status: str,
    jobs_fetched: int,
    jobs_inserted: int,
    jobs_skipped: int,
    error_message: str | None = None,
) -> None:
    """Update the sync_log entry with final results."""
    db.execute(
        """
        UPDATE sync_log
        SET completed_at = ?, status = ?, jobs_fetched = ?,
            jobs_inserted = ?, jobs_skipped = ?, error_message = ?
        WHERE id = ?
        """,
        (
            datetime.now(timezone.utc).isoformat(),
            status,
            jobs_fetched,
            jobs_inserted,
            jobs_skipped,
            error_message,
            sync_id,
        ),
    )
    db.commit()


def _upsert_job(
    db: sqlite3.Connection,
    job: AdzunaJob,
    canonical_role: str,
    salary_min: float | None,
    salary_max: float | None,
    salary_is_estimated: bool,
    skills: list[tuple[str, str, float]],
) -> bool:
    """Insert a job into raw_jobs. Returns True if inserted, False if duplicate."""
    cursor = db.execute(
        """
        INSERT OR IGNORE INTO raw_jobs
            (adzuna_id, title, company, location_city, location_region,
             location_lat, location_lon, salary_min, salary_max,
             salary_is_estimated, description, canonical_role, source, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'adzuna', ?)
        """,
        (
            job.id,
            job.title,
            job.company,
            job.location_city,
            job.location_region,
            job.location_lat,
            job.location_lon,
            salary_min,
            salary_max,
            1 if salary_is_estimated else 0,
            job.description,
            canonical_role,
            job.created,
        ),
    )

    if cursor.rowcount == 0:
        return False

    job_id = cursor.lastrowid
    for skill_raw, skill_norm, confidence in skills:
        db.execute(
            "INSERT INTO job_skills (job_id, skill_raw, skill_norm, confidence) VALUES (?, ?, ?, ?)",
            (job_id, skill_raw, skill_norm, confidence),
        )

    db.commit()
    return True


def _rebuild_cooccurrence(db: sqlite3.Connection) -> int:
    """Rebuild the skill_cooccurrence table from scratch. Returns pair count."""
    db.execute("DELETE FROM skill_cooccurrence")
    cursor = db.execute(
        """
        INSERT INTO skill_cooccurrence (skill_a, skill_b, count, updated_at)
        SELECT a.skill_norm, b.skill_norm, COUNT(*), CURRENT_TIMESTAMP
        FROM job_skills a
        JOIN job_skills b ON a.job_id = b.job_id AND a.skill_norm < b.skill_norm
        GROUP BY a.skill_norm, b.skill_norm
        HAVING COUNT(*) >= 2
        """
    )
    db.commit()
    return cursor.rowcount


async def _fetch_query_pages(
    client: AdzunaClient,
    query: str,
    location: str,
    max_pages: int,
) -> list[AdzunaJob]:
    """Fetch multiple pages for a single search query."""
    all_jobs: list[AdzunaJob] = []

    for page in range(1, max_pages + 1):
        try:
            jobs = await client.fetch_jobs(
                query=query,
                location=location,
                page=page,
                results_per_page=settings.adzuna_results_per_page,
            )
            if not jobs:
                break
            all_jobs.extend(jobs)
            logger.info(
                "Fetched page %d for '%s': %d jobs", page, query, len(jobs)
            )
            # Rate limit: 1 second between requests
            await asyncio.sleep(1)
        except RateLimitError:
            logger.warning("Rate limited on query '%s' page %d, stopping", query, page)
            break
        except Exception as e:
            logger.error("Error fetching '%s' page %d: %s", query, page, e)
            break

    return all_jobs


async def run_sync(db: sqlite3.Connection) -> None:
    """Run the full sync pipeline: fetch → normalize → extract → upsert → rebuild."""
    creds = get_credentials()
    if creds is None:
        sync_id = _create_sync_log(db)
        _update_sync_log(db, sync_id, "error", 0, 0, 0, "No credentials configured")
        logger.error("Sync aborted: no Adzuna credentials")
        return

    sync_id = _create_sync_log(db)
    app_id, app_key = creds
    client = AdzunaClient(app_id, app_key, settings.adzuna_country)
    normalizer = RoleNormalizer()
    pipeline = get_pipeline()

    total_fetched = 0
    total_inserted = 0
    total_skipped = 0
    errors: list[str] = []

    pages_per_query = max(1, settings.adzuna_max_pages_per_run // len(SEARCH_QUERIES))

    try:
        for query, location in SEARCH_QUERIES:
            jobs = await _fetch_query_pages(client, query, location, pages_per_query)
            total_fetched += len(jobs)

            for job in jobs:
                try:
                    canonical_role = normalizer.normalize(job.title)
                    skill_matches = pipeline.extract_skills(job.description)
                    skills = [
                        (s.skill_raw, s.skill_norm, s.confidence)
                        for s in skill_matches
                    ]
                    sal_min, sal_max, is_estimated = resolve_salary(
                        job.salary_min, job.salary_max, canonical_role
                    )
                    inserted = _upsert_job(
                        db, job, canonical_role, sal_min, sal_max, is_estimated, skills
                    )
                    if inserted:
                        total_inserted += 1
                    else:
                        total_skipped += 1
                except Exception as e:
                    logger.error("Failed processing job %s: %s", job.id, e)
                    errors.append(f"Job {job.id}: {e}")
                    total_skipped += 1

        cooccurrence_count = _rebuild_cooccurrence(db)
        logger.info("Rebuilt co-occurrence table: %d pairs", cooccurrence_count)

        status = "success" if not errors else "partial"
        error_msg = "; ".join(errors[:10]) if errors else None
        _update_sync_log(
            db, sync_id, status, total_fetched, total_inserted, total_skipped, error_msg
        )
        logger.info(
            "Sync complete: fetched=%d inserted=%d skipped=%d status=%s",
            total_fetched, total_inserted, total_skipped, status,
        )

    except Exception as e:
        logger.error("Sync failed: %s", e)
        _update_sync_log(
            db, sync_id, "error", total_fetched, total_inserted, total_skipped, str(e)
        )
