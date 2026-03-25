"""Tests for the Adzuna API client."""

import json
from pathlib import Path

import httpx
import pytest
import respx

from services.adzuna_client import AdzunaClient, AdzunaJob, RateLimitError

FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture() -> dict:
    with open(FIXTURES / "adzuna_response.json", encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture
def client() -> AdzunaClient:
    return AdzunaClient(app_id="test_id", app_key="test_key", country="us")


@pytest.mark.asyncio
@respx.mock
async def test_fetch_jobs_success(client: AdzunaClient) -> None:
    """Successful fetch returns parsed AdzunaJob list."""
    fixture = _load_fixture()
    respx.get("https://api.adzuna.com/v1/api/jobs/us/search/1").mock(
        return_value=httpx.Response(200, json=fixture)
    )

    jobs = await client.fetch_jobs("software engineer")

    assert len(jobs) == 5
    assert all(isinstance(j, AdzunaJob) for j in jobs)


@pytest.mark.asyncio
@respx.mock
async def test_fetch_jobs_parses_full_record(client: AdzunaClient) -> None:
    """First fixture job has all fields populated."""
    fixture = _load_fixture()
    respx.get("https://api.adzuna.com/v1/api/jobs/us/search/1").mock(
        return_value=httpx.Response(200, json=fixture)
    )

    jobs = await client.fetch_jobs("software engineer")
    job = jobs[0]

    assert job.id == "4012345678"
    assert job.title == "Senior Software Engineer"
    assert job.company == "Acme Corp"
    assert job.location_region == "US"
    assert job.location_city == "San Francisco"
    assert job.location_lat == pytest.approx(37.7749)
    assert job.location_lon == pytest.approx(-122.4194)
    assert job.salary_min == 140000
    assert job.salary_max == 180000


@pytest.mark.asyncio
@respx.mock
async def test_fetch_jobs_handles_null_company(client: AdzunaClient) -> None:
    """Job with null company parses correctly."""
    fixture = _load_fixture()
    respx.get("https://api.adzuna.com/v1/api/jobs/us/search/1").mock(
        return_value=httpx.Response(200, json=fixture)
    )

    jobs = await client.fetch_jobs("devops")
    devops_job = [j for j in jobs if j.title == "DevOps Engineer"][0]

    assert devops_job.company is None


@pytest.mark.asyncio
@respx.mock
async def test_fetch_jobs_handles_missing_salary(client: AdzunaClient) -> None:
    """Job without salary fields returns None."""
    fixture = _load_fixture()
    respx.get("https://api.adzuna.com/v1/api/jobs/us/search/1").mock(
        return_value=httpx.Response(200, json=fixture)
    )

    jobs = await client.fetch_jobs("devops")
    devops_job = [j for j in jobs if j.title == "DevOps Engineer"][0]

    assert devops_job.salary_min is None
    assert devops_job.salary_max is None


@pytest.mark.asyncio
@respx.mock
async def test_fetch_jobs_handles_empty_area(client: AdzunaClient) -> None:
    """Job with empty location area list returns None for city/region."""
    fixture = _load_fixture()
    respx.get("https://api.adzuna.com/v1/api/jobs/us/search/1").mock(
        return_value=httpx.Response(200, json=fixture)
    )

    jobs = await client.fetch_jobs("it support")
    it_job = [j for j in jobs if j.title == "IT Support Specialist"][0]

    assert it_job.location_city is None
    assert it_job.location_region is None


@pytest.mark.asyncio
@respx.mock
async def test_fetch_jobs_empty_results(client: AdzunaClient) -> None:
    """Empty results array returns empty list."""
    respx.get("https://api.adzuna.com/v1/api/jobs/us/search/1").mock(
        return_value=httpx.Response(200, json={"results": [], "count": 0})
    )

    jobs = await client.fetch_jobs("nonexistent role xyz")

    assert jobs == []


@pytest.mark.asyncio
@respx.mock
async def test_fetch_jobs_rate_limit_raises(client: AdzunaClient) -> None:
    """HTTP 429 raises RateLimitError."""
    respx.get("https://api.adzuna.com/v1/api/jobs/us/search/1").mock(
        return_value=httpx.Response(429, text="Rate limit exceeded")
    )

    with pytest.raises(RateLimitError):
        await client.fetch_jobs("software engineer")


@pytest.mark.asyncio
@respx.mock
async def test_fetch_jobs_server_error_raises(client: AdzunaClient) -> None:
    """HTTP 500 raises HTTPStatusError."""
    respx.get("https://api.adzuna.com/v1/api/jobs/us/search/1").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )

    with pytest.raises(httpx.HTTPStatusError):
        await client.fetch_jobs("software engineer")


@pytest.mark.asyncio
@respx.mock
async def test_fetch_jobs_malformed_result_skipped(client: AdzunaClient) -> None:
    """Malformed job entries are silently skipped."""
    respx.get("https://api.adzuna.com/v1/api/jobs/us/search/1").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {"bad": "data"},  # Missing required fields
                    {
                        "id": 999,
                        "title": "Good Job",
                        "description": "Valid entry",
                        "created": "2024-01-01",
                        "location": {},
                    },
                ]
            },
        )
    )

    jobs = await client.fetch_jobs("test")

    assert len(jobs) == 1
    assert jobs[0].title == "Good Job"


@pytest.mark.asyncio
@respx.mock
async def test_fetch_jobs_pagination_param(client: AdzunaClient) -> None:
    """Page parameter is passed in the URL."""
    route = respx.get("https://api.adzuna.com/v1/api/jobs/us/search/3").mock(
        return_value=httpx.Response(200, json={"results": [], "count": 0})
    )

    await client.fetch_jobs("test", page=3)

    assert route.called


@pytest.mark.asyncio
@respx.mock
async def test_fetch_jobs_location_param(client: AdzunaClient) -> None:
    """Location parameter is passed as 'where' query param."""
    route = respx.get("https://api.adzuna.com/v1/api/jobs/us/search/1").mock(
        return_value=httpx.Response(200, json={"results": [], "count": 0})
    )

    await client.fetch_jobs("test", location="San Francisco")

    assert route.called
    request = route.calls[0].request
    assert "where=San+Francisco" in str(request.url) or "where=San%20Francisco" in str(
        request.url
    )


@pytest.mark.asyncio
@respx.mock
async def test_fetch_jobs_single_area_entry(client: AdzunaClient) -> None:
    """Location with single area entry sets region but not city."""
    respx.get("https://api.adzuna.com/v1/api/jobs/us/search/1").mock(
        return_value=httpx.Response(200, json=_load_fixture())
    )

    jobs = await client.fetch_jobs("product")
    pm_job = [j for j in jobs if j.title == "Product Manager"][0]

    assert pm_job.location_region == "US"
    assert pm_job.location_city is None  # Only 1 area entry → no city
