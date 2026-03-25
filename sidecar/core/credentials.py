"""In-memory credential store for Adzuna API keys."""

_app_id: str | None = None
_app_key: str | None = None


def set_credentials(app_id: str, app_key: str) -> None:
    global _app_id, _app_key  # noqa: PLW0603
    _app_id = app_id
    _app_key = app_key


def get_credentials() -> tuple[str, str] | None:
    if _app_id is None or _app_key is None:
        return None
    return (_app_id, _app_key)


def has_credentials() -> bool:
    return _app_id is not None and _app_key is not None
