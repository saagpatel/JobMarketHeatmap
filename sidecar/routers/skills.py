"""Skill demand and co-occurrence endpoints."""

import logging

from fastapi import APIRouter, Query
from pydantic import BaseModel

from core.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["skills"])


class SkillDemand(BaseModel):
    skill_norm: str
    count: int
    pct_of_postings: float


class CoOccurrencePair(BaseModel):
    skill_a: str
    skill_b: str
    count: int
    weight: float


@router.get("/skills/demand", response_model=list[SkillDemand])
async def skill_demand(
    canonical_role: str | None = Query(None),
    location_region: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    limit: int = Query(20, ge=1, le=200),
) -> list[SkillDemand]:
    """Top skills by posting count with optional filters."""
    db = get_db()

    conditions: list[str] = []
    params: list[str | int | float] = []

    if canonical_role is not None:
        conditions.append("r.canonical_role = ?")
        params.append(canonical_role)
    if location_region is not None:
        conditions.append("r.location_region = ?")
        params.append(location_region)
    if date_from is not None:
        conditions.append("r.fetched_at >= ?")
        params.append(date_from)
    if date_to is not None:
        conditions.append("r.fetched_at <= ?")
        params.append(date_to)

    where_clause = (" WHERE " + " AND ".join(conditions)) if conditions else ""

    # Total filtered jobs for percentage calculation
    total_row = db.execute(
        f"SELECT COUNT(DISTINCT r.id) as cnt FROM raw_jobs r{where_clause}",  # noqa: S608
        params,
    ).fetchone()
    total_jobs: int = total_row["cnt"] if total_row else 0

    if total_jobs == 0:
        return []

    # Join with job_skills, apply same filters, group by skill_norm
    join_where = (
        " WHERE " + " AND ".join(conditions)
    ) if conditions else ""

    rows = db.execute(
        f"""
        SELECT js.skill_norm, COUNT(DISTINCT r.id) as count
        FROM job_skills js
        JOIN raw_jobs r ON r.id = js.job_id
        {join_where}
        GROUP BY js.skill_norm
        ORDER BY count DESC
        LIMIT ?
        """,  # noqa: S608
        [*params, limit],
    ).fetchall()

    return [
        SkillDemand(
            skill_norm=row["skill_norm"],
            count=row["count"],
            pct_of_postings=round(row["count"] / total_jobs * 100, 1),
        )
        for row in rows
    ]


@router.get("/skills/cooccurrence", response_model=list[CoOccurrencePair])
async def skill_cooccurrence(
    limit: int = Query(200, ge=1, le=1000),
) -> list[CoOccurrencePair]:
    """Top skill co-occurrence pairs, with weight normalized to 0-1."""
    db = get_db()

    rows = db.execute(
        """
        SELECT skill_a, skill_b, count
        FROM skill_cooccurrence
        ORDER BY count DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    if not rows:
        return []

    max_count: int = rows[0]["count"]

    return [
        CoOccurrencePair(
            skill_a=row["skill_a"],
            skill_b=row["skill_b"],
            count=row["count"],
            weight=round(row["count"] / max_count, 4) if max_count > 0 else 0.0,
        )
        for row in rows
    ]
