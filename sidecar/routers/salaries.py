"""Salary distribution endpoints — box-plot stats per role."""

import logging
from math import floor

from fastapi import APIRouter, Query
from pydantic import BaseModel

from core.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["salaries"])

MIN_SAMPLE_SIZE = 3


class SalaryBucket(BaseModel):
    role: str
    p25: float
    median: float
    p75: float
    min: float
    max: float
    sample_size: int


def _percentile(sorted_values: list[float], pct: float) -> float:
    """Calculate percentile from a pre-sorted list using linear interpolation."""
    n = len(sorted_values)
    idx = pct / 100.0 * (n - 1)
    lower = floor(idx)
    upper = lower + 1
    if upper >= n:
        return sorted_values[-1]
    frac = idx - lower
    return sorted_values[lower] + frac * (sorted_values[upper] - sorted_values[lower])


@router.get("/salaries/distribution", response_model=list[SalaryBucket])
async def salary_distribution(
    canonical_role: str | None = Query(None),
    location_region: str | None = Query(None),
) -> list[SalaryBucket]:
    """Salary stats (p25/median/p75/min/max) per canonical role."""
    db = get_db()

    conditions: list[str] = ["salary_min IS NOT NULL"]
    params: list[str | int | float] = []

    if canonical_role is not None:
        conditions.append("canonical_role = ?")
        params.append(canonical_role)
    if location_region is not None:
        conditions.append("location_region = ?")
        params.append(location_region)

    where_clause = " WHERE " + " AND ".join(conditions)

    rows = db.execute(
        f"""
        SELECT canonical_role, salary_min
        FROM raw_jobs
        {where_clause}
        AND canonical_role IS NOT NULL
        ORDER BY canonical_role, salary_min
        """,  # noqa: S608
        params,
    ).fetchall()

    # Group salaries by role
    role_salaries: dict[str, list[float]] = {}
    for row in rows:
        role: str = row["canonical_role"]
        role_salaries.setdefault(role, []).append(float(row["salary_min"]))

    results: list[SalaryBucket] = []
    for role, salaries in sorted(role_salaries.items()):
        if len(salaries) < MIN_SAMPLE_SIZE:
            continue
        # Already sorted from SQL ORDER BY
        results.append(
            SalaryBucket(
                role=role,
                p25=round(_percentile(salaries, 25), 0),
                median=round(_percentile(salaries, 50), 0),
                p75=round(_percentile(salaries, 75), 0),
                min=salaries[0],
                max=salaries[-1],
                sample_size=len(salaries),
            )
        )

    return results
