"""SQLite database connection and migration runner."""

import logging
import sqlite3
from pathlib import Path

from core.config import settings

logger = logging.getLogger(__name__)

_connection: sqlite3.Connection | None = None

MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"


def _ensure_data_dir() -> None:
    """Create the data directory if it doesn't exist."""
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)


def _run_migrations(conn: sqlite3.Connection) -> None:
    """Apply any unapplied SQL migration files in order."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS _migrations (
            filename    TEXT PRIMARY KEY,
            applied_at  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    applied = {
        row[0] for row in conn.execute("SELECT filename FROM _migrations").fetchall()
    }

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    for migration_file in migration_files:
        if migration_file.name not in applied:
            logger.info("Applying migration: %s", migration_file.name)
            sql = migration_file.read_text()
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO _migrations (filename) VALUES (?)",
                (migration_file.name,),
            )
            conn.commit()
            logger.info("Migration applied: %s", migration_file.name)


def get_db() -> sqlite3.Connection:
    """Get or create the SQLite connection. Runs migrations on first call."""
    global _connection  # noqa: PLW0603

    if _connection is not None:
        return _connection

    _ensure_data_dir()

    conn = sqlite3.connect(str(settings.db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    _run_migrations(conn)

    _connection = conn
    logger.info("Database initialized at %s", settings.db_path)
    return conn


def is_db_connected() -> bool:
    """Check whether the database connection is alive."""
    if _connection is None:
        return False
    try:
        _connection.execute("SELECT 1")
        return True
    except sqlite3.Error:
        return False
