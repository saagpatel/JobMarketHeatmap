"""Adzuna job search API client."""

from __future__ import annotations

import logging
from typing import Any

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

BASE_URL = "https://api.adzuna.com/v1/api/jobs"


class RateLimitError(Exception):
    """Raised when the Adzuna API returns HTTP 429."""


class AdzunaJob(BaseModel):
    """Parsed job listing from the Adzuna API."""

    id: str
    title: str
    company: str | None = None
    location_city: str | None = None
    location_region: str | None = None
    location_lat: float | None = None
    location_lon: float | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    description: str
    created: str


def _parse_job(raw: dict[str, Any]) -> AdzunaJob:
    """Parse a single job result from the Adzuna API response."""
    location = raw.get("location", {})
    area: list[str] = location.get("area", [])
    region = area[0] if len(area) >= 1 else None
    city = area[-1] if len(area) >= 2 else None

    company_data = raw.get("company", {})
    company_name = company_data.get("display_name") if company_data else None

    return AdzunaJob(
        id=str(raw["id"]),
        title=raw.get("title", ""),
        company=company_name,
        location_city=city,
        location_region=region,
        location_lat=location.get("latitude"),
        location_lon=location.get("longitude"),
        salary_min=raw.get("salary_min"),
        salary_max=raw.get("salary_max"),
        description=raw.get("description", ""),
        created=raw.get("created", ""),
    )


class AdzunaClient:
    """Async client for the Adzuna job search API."""

    def __init__(self, app_id: str, app_key: str, country: str = "us") -> None:
        self.app_id = app_id
        self.app_key = app_key
        self.country = country
        self._client = httpx.AsyncClient(timeout=30.0)

    async def fetch_jobs(
        self,
        query: str,
        location: str = "",
        page: int = 1,
        results_per_page: int = 50,
    ) -> list[AdzunaJob]:
        """Fetch job listings from the Adzuna API.

        Args:
            query: Search query string.
            location: Optional location filter.
            page: Page number (1-based).
            results_per_page: Number of results per page.

        Returns:
            List of parsed AdzunaJob objects.

        Raises:
            RateLimitError: If the API returns HTTP 429.
            httpx.HTTPStatusError: For other non-2xx responses.
        """
        url = f"{BASE_URL}/{self.country}/search/{page}"
        params: dict[str, str | int] = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "what": query,
            "results_per_page": results_per_page,
        }
        if location:
            params["where"] = location

        response = await self._client.get(url, params=params)

        if response.status_code == 429:
            raise RateLimitError(
                f"Adzuna API rate limit exceeded (HTTP 429): {response.text}"
            )

        response.raise_for_status()

        data = response.json()
        results: list[dict[str, Any]] = data.get("results", [])

        jobs: list[AdzunaJob] = []
        for raw in results:
            try:
                jobs.append(_parse_job(raw))
            except (KeyError, ValueError) as exc:
                logger.warning("Skipping malformed job result: %s", exc)

        return jobs

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()
