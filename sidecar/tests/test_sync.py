"""Integration tests for the sync orchestrator."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.adzuna_client import AdzunaJob
from services.sync_orchestrator import (
    _rebuild_cooccurrence,
    _upsert_job,
    run_sync,
)


def _make_job(
    job_id: str = "123",
    title: str = "Senior Software Engineer",
    description: str = "We need Python and Kubernetes experience.",
    salary_min: float | None = 120000,
    salary_max: float | None = 180000,
    company: str | None = "Acme Corp",
    city: str | None = "San Francisco",
    region: str | None = "California",
    lat: float | None = 37.7749,
    lon: float | None = -122.4194,
) -> AdzunaJob:
    return AdzunaJob(
        id=job_id,
        title=title,
        company=company,
        location_city=city,
        location_region=region,
        location_lat=lat,
        location_lon=lon,
        salary_min=salary_min,
        salary_max=salary_max,
        description=description,
        created="2025-01-15T10:00:00Z",
    )


class TestUpsertJob:
    def test_insert_new_job(self, test_db):
        job = _make_job()
        skills = [("Python", "Python", 1.0), ("Kubernetes", "Kubernetes", 1.0)]
        result = _upsert_job(test_db, job, "Senior Software Engineer", 120000, 180000, False, skills)
        assert result is True

        row = test_db.execute("SELECT * FROM raw_jobs WHERE adzuna_id = '123'").fetchone()
        assert row is not None
        assert row["title"] == "Senior Software Engineer"
        assert row["canonical_role"] == "Senior Software Engineer"

        skill_rows = test_db.execute("SELECT * FROM job_skills WHERE job_id = ?", (row["id"],)).fetchall()
        assert len(skill_rows) == 2

    def test_duplicate_is_skipped(self, test_db):
        job = _make_job()
        _upsert_job(test_db, job, "Software Engineer", 120000, 180000, False, [])
        result = _upsert_job(test_db, job, "Software Engineer", 120000, 180000, False, [])
        assert result is False

        count = test_db.execute("SELECT COUNT(*) FROM raw_jobs").fetchone()[0]
        assert count == 1

    def test_estimated_salary_flag(self, test_db):
        job = _make_job(salary_min=None, salary_max=None)
        _upsert_job(test_db, job, "Software Engineer", 105816, 158724, True, [])

        row = test_db.execute("SELECT salary_is_estimated FROM raw_jobs WHERE adzuna_id = '123'").fetchone()
        assert row["salary_is_estimated"] == 1


class TestRebuildCooccurrence:
    def test_builds_pairs(self, test_db):
        # Insert 2 jobs with overlapping skills
        for i, desc in enumerate(["job1", "job2"]):
            test_db.execute(
                "INSERT INTO raw_jobs (adzuna_id, title, description) VALUES (?, ?, ?)",
                (f"id{i}", "Test", desc),
            )
        test_db.commit()

        # Both jobs have Python and Docker
        for job_id in [1, 2]:
            test_db.execute(
                "INSERT INTO job_skills (job_id, skill_raw, skill_norm) VALUES (?, 'Python', 'Python')",
                (job_id,),
            )
            test_db.execute(
                "INSERT INTO job_skills (job_id, skill_raw, skill_norm) VALUES (?, 'Docker', 'Docker')",
                (job_id,),
            )
        test_db.commit()

        count = _rebuild_cooccurrence(test_db)
        assert count >= 1

        row = test_db.execute(
            "SELECT * FROM skill_cooccurrence WHERE skill_a = 'Docker' AND skill_b = 'Python'"
        ).fetchone()
        assert row is not None
        assert row["count"] == 2

    def test_no_self_pairs(self, test_db):
        test_db.execute(
            "INSERT INTO raw_jobs (adzuna_id, title, description) VALUES ('1', 'Test', 'desc')"
        )
        test_db.execute(
            "INSERT INTO job_skills (job_id, skill_raw, skill_norm) VALUES (1, 'Python', 'Python')"
        )
        test_db.commit()

        count = _rebuild_cooccurrence(test_db)
        assert count == 0


@pytest.mark.asyncio
class TestRunSync:
    async def test_sync_without_credentials(self, test_db):
        with patch("services.sync_orchestrator.get_credentials", return_value=None):
            await run_sync(test_db)

        row = test_db.execute("SELECT * FROM sync_log ORDER BY id DESC LIMIT 1").fetchone()
        assert row["status"] == "error"
        assert "credentials" in row["error_message"].lower()

    async def test_sync_with_mocked_adzuna(self, test_db):
        mock_jobs = [
            _make_job(job_id=f"job{i}", title=title, description=desc)
            for i, (title, desc) in enumerate([
                ("Software Engineer", "Need Python and React skills"),
                ("DevOps Engineer", "Kubernetes and Docker required"),
                ("Data Scientist", "Machine learning and Python experience"),
            ])
        ]

        with (
            patch("services.sync_orchestrator.get_credentials", return_value=("id", "key")),
            patch("services.sync_orchestrator._fetch_query_pages", new_callable=AsyncMock) as mock_fetch,
        ):
            # Return different jobs for each query
            mock_fetch.side_effect = [mock_jobs[:1], mock_jobs[1:2], mock_jobs[2:]]
            await run_sync(test_db)

        # Check sync_log
        log = test_db.execute("SELECT * FROM sync_log ORDER BY id DESC LIMIT 1").fetchone()
        assert log["status"] in ("success", "partial")
        assert log["jobs_fetched"] == 3
        assert log["jobs_inserted"] == 3

        # Check raw_jobs
        count = test_db.execute("SELECT COUNT(*) FROM raw_jobs").fetchone()[0]
        assert count == 3

        # Check job_skills populated
        skill_count = test_db.execute("SELECT COUNT(*) FROM job_skills").fetchone()[0]
        assert skill_count > 0

        # Check canonical_role assigned
        unknown_count = test_db.execute(
            "SELECT COUNT(*) FROM raw_jobs WHERE canonical_role = 'UNKNOWN'"
        ).fetchone()[0]
        assert unknown_count <= 1  # at most 1 UNKNOWN
