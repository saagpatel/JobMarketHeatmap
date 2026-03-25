"""Job listing endpoints — paginated browsing with filters."""

import logging

from fastapi import APIRouter, Query
from pydantic import BaseModel

from core.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["jobs"])


class JobItem(BaseModel):
    id: int
    adzuna_id: str
    title: str
    company: str | None = None
    location_city: str | None = None
    location_region: str | None = None
    location_lat: float | None = None
    location_lon: float | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_is_estimated: bool = False
    canonical_role: str | None = None
    source: str = "adzuna"
    fetched_at: str
    created_at: str


class JobListMeta(BaseModel):
    total: int
    has_more: bool


class JobListResponse(BaseModel):
    data: list[JobItem]
    meta: JobListMeta


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    canonical_role: str | None = Query(None),
    location_region: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    cursor: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> JobListResponse:
    """Paginated job listings with optional filters."""
    db = get_db()

    conditions: list[str] = []
    params: list[str | int | float] = []

    if canonical_role is not None:
        conditions.append("canonical_role = ?")
        params.append(canonical_role)
    if location_region is not None:
        conditions.append("location_region = ?")
        params.append(location_region)
    if date_from is not None:
        conditions.append("fetched_at >= ?")
        params.append(date_from)
    if date_to is not None:
        conditions.append("fetched_at <= ?")
        params.append(date_to)

    where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""

    total_row = db.execute(
        f"SELECT COUNT(*) as cnt FROM raw_jobs{where_clause}",  # noqa: S608
        params,
    ).fetchone()
    total: int = total_row["cnt"] if total_row else 0

    rows = db.execute(
        f"""
        SELECT id, adzuna_id, title, company, location_city, location_region,
               location_lat, location_lon, salary_min, salary_max,
               salary_is_estimated, canonical_role, source, fetched_at, created_at
        FROM raw_jobs{where_clause}
        ORDER BY fetched_at DESC
        LIMIT ? OFFSET ?
        """,  # noqa: S608
        [*params, limit, cursor],
    ).fetchall()

    data = [
        JobItem(
            id=r["id"],
            adzuna_id=r["adzuna_id"],
            title=r["title"],
            company=r["company"],
            location_city=r["location_city"],
            location_region=r["location_region"],
            location_lat=r["location_lat"],
            location_lon=r["location_lon"],
            salary_min=r["salary_min"],
            salary_max=r["salary_max"],
            salary_is_estimated=bool(r["salary_is_estimated"]),
            canonical_role=r["canonical_role"],
            source=r["source"],
            fetched_at=r["fetched_at"],
            created_at=r["created_at"],
        )
        for r in rows
    ]

    return JobListResponse(
        data=data,
        meta=JobListMeta(total=total, has_more=(cursor + limit) < total),
    )


@router.get("/roles", response_model=list[str])
async def list_roles() -> list[str]:
    """Distinct canonical roles, excluding UNKNOWN."""
    db = get_db()
    rows = db.execute(
        """
        SELECT DISTINCT canonical_role
        FROM raw_jobs
        WHERE canonical_role IS NOT NULL AND canonical_role != 'UNKNOWN'
        ORDER BY canonical_role
        """
    ).fetchall()
    return [r["canonical_role"] for r in rows]


@router.get("/regions", response_model=list[str])
async def list_regions() -> list[str]:
    """Distinct location regions, excluding NULL."""
    db = get_db()
    rows = db.execute(
        """
        SELECT DISTINCT location_region
        FROM raw_jobs
        WHERE location_region IS NOT NULL
        ORDER BY location_region
        """
    ).fetchall()
    return [r["location_region"] for r in rows]
