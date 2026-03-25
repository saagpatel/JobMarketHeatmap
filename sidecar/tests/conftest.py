"""Shared test fixtures."""

import sqlite3
import sys
from pathlib import Path

import pytest

# Ensure sidecar/ is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"


@pytest.fixture
def test_db() -> sqlite3.Connection:
    """In-memory SQLite database with all migrations applied."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    for sql_file in sorted(MIGRATIONS_DIR.glob("*.sql")):
        conn.executescript(sql_file.read_text())
    yield conn  # type: ignore[misc]
    conn.close()


@pytest.fixture(scope="module")
def nlp():  # type: ignore[no-untyped-def]
    """Module-scoped NLP pipeline singleton (expensive to load)."""
    from services.nlp_pipeline import get_pipeline

    return get_pipeline()
