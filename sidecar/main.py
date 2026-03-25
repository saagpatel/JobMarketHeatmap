"""FastAPI sidecar for Job Market Heatmap — serves job data from local SQLite."""

import os
import signal
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.db import get_db, is_db_connected
from core.scheduler import setup_scheduler, shutdown_scheduler
from routers.credentials import router as credentials_router
from routers.geo import router as geo_router
from routers.jobs import router as jobs_router
from routers.salaries import router as salaries_router
from routers.skills import router as skills_router
from routers.sync import router as sync_router
from routers.trends import router as trends_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Initialize database and scheduler on startup."""
    get_db()
    setup_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(title="Job Market Heatmap Sidecar", version="0.1.0", lifespan=lifespan)

app.include_router(credentials_router)
app.include_router(geo_router)
app.include_router(jobs_router)
app.include_router(salaries_router)
app.include_router(skills_router)
app.include_router(sync_router)
app.include_router(trends_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:1420", "tauri://localhost"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, object]:
    return {
        "status": "ok",
        "db_connected": is_db_connected(),
        "port": settings.port,
    }


@app.post("/shutdown")
async def shutdown() -> dict[str, str]:
    """Graceful shutdown — called by Tauri before killing the sidecar process."""
    os.kill(os.getpid(), signal.SIGTERM)
    return {"status": "shutting_down"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=settings.port)
