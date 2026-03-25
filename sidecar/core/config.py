"""Pydantic settings for the sidecar process."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    db_path: Path = Path.home() / ".job-market-heatmap" / "data.db"
    port: int = 8008
    sync_hour: int = 2
    sync_minute: int = 0
    adzuna_results_per_page: int = 50
    adzuna_max_pages_per_run: int = 20
    adzuna_country: str = "us"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
