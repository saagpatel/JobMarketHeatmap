"""Credential management endpoints — stores Adzuna API keys in memory."""

from fastapi import APIRouter
from pydantic import BaseModel

from core.credentials import has_credentials
from core.credentials import set_credentials as store_credentials

router = APIRouter(prefix="/api/v1", tags=["credentials"])


class CredentialPayload(BaseModel):
    app_id: str
    app_key: str


class CredentialResponse(BaseModel):
    status: str


class CredentialStatusResponse(BaseModel):
    has_credentials: bool


@router.post("/credentials", status_code=200, response_model=CredentialResponse)
async def set_credentials(payload: CredentialPayload) -> CredentialResponse:
    store_credentials(payload.app_id, payload.app_key)
    return CredentialResponse(status="ok")


@router.get("/credentials/status", response_model=CredentialStatusResponse)
async def credentials_status() -> CredentialStatusResponse:
    return CredentialStatusResponse(has_credentials=has_credentials())
