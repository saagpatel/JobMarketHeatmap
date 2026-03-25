"""Geographic density endpoints — job counts by location."""

import logging

from fastapi import APIRouter, Query
from pydantic import BaseModel

from core.db import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["geo"])


class GeoPoint(BaseModel):
    lat: float
    lon: float
    city: str | None = None
    count: int


@router.get("/geo/density", response_model=list[GeoPoint])
async def geo_density(
    canonical_role: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
) -> list[GeoPoint]:
    """Job density grouped by rounded lat/lon (2 decimal places)."""
    db = get_db()

    conditions: list[str] = [
        "location_lat IS NOT NULL",
        "location_lon IS NOT NULL",
    ]
    params: list[str | int | float] = []

    if canonical_role is not None:
        conditions.append("canonical_role = ?")
        params.append(canonical_role)
    if date_from is not None:
        conditions.append("fetched_at >= ?")
        params.append(date_from)
    if date_to is not None:
        conditions.append("fetched_at <= ?")
        params.append(date_to)

    where_clause = " WHERE " + " AND ".join(conditions)

    rows = db.execute(
        f"""
        SELECT
            ROUND(location_lat, 2) as lat,
            ROUND(location_lon, 2) as lon,
            location_city as city,
            COUNT(*) as count
        FROM raw_jobs
        {where_clause}
        GROUP BY ROUND(location_lat, 2), ROUND(location_lon, 2)
        ORDER BY count DESC
        """,  # noqa: S608
        params,
    ).fetchall()

    return [
        GeoPoint(
            lat=row["lat"],
            lon=row["lon"],
            city=row["city"],
            count=row["count"],
        )
        for row in rows
    ]
