"""Trend endpoints — weekly skill counts over time."""

import logging

from fastapi import APIRouter, Query
from pydantic import BaseModel

from core.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["trends"])


class TrendPoint(BaseModel):
    week: str
    skill: str
    count: int


@router.get("/trends/skills", response_model=list[TrendPoint])
async def skill_trends(
    skills: str | None = Query(None, description="Comma-separated skill names"),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    limit: int = Query(5, ge=1, le=50),
) -> list[TrendPoint]:
    """Weekly skill counts over time. Auto-selects top N skills if none specified."""
    db = get_db()

    # Determine which skills to chart
    if skills is not None:
        skill_list = [s.strip() for s in skills.split(",") if s.strip()]
    else:
        # Auto-select top N skills by total count
        date_conditions: list[str] = []
        date_params: list[str | int | float] = []
        if date_from is not None:
            date_conditions.append("r.fetched_at >= ?")
            date_params.append(date_from)
        if date_to is not None:
            date_conditions.append("r.fetched_at <= ?")
            date_params.append(date_to)

        date_where = (
            " WHERE " + " AND ".join(date_conditions)
        ) if date_conditions else ""

        top_rows = db.execute(
            f"""
            SELECT js.skill_norm, COUNT(*) as cnt
            FROM job_skills js
            JOIN raw_jobs r ON r.id = js.job_id
            {date_where}
            GROUP BY js.skill_norm
            ORDER BY cnt DESC
            LIMIT ?
            """,  # noqa: S608
            [*date_params, limit],
        ).fetchall()
        skill_list = [row["skill_norm"] for row in top_rows]

    if not skill_list:
        return []

    # Build parameterized IN clause
    placeholders = ", ".join("?" for _ in skill_list)
    conditions: list[str] = [f"js.skill_norm IN ({placeholders})"]
    params: list[str | int | float] = list(skill_list)

    if date_from is not None:
        conditions.append("r.fetched_at >= ?")
        params.append(date_from)
    if date_to is not None:
        conditions.append("r.fetched_at <= ?")
        params.append(date_to)

    where_clause = " WHERE " + " AND ".join(conditions)

    rows = db.execute(
        f"""
        SELECT strftime('%Y-W%W', r.fetched_at) as week,
               js.skill_norm as skill,
               COUNT(*) as count
        FROM job_skills js
        JOIN raw_jobs r ON r.id = js.job_id
        {where_clause}
        GROUP BY week, js.skill_norm
        ORDER BY week, js.skill_norm
        """,  # noqa: S608
        params,
    ).fetchall()

    return [
        TrendPoint(week=row["week"], skill=row["skill"], count=row["count"])
        for row in rows
    ]
