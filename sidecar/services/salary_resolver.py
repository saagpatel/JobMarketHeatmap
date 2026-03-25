"""Salary resolution using explicit values or BLS wage estimates."""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"

_BLS_WAGES_PATH = DATA_DIR / "bls_wages_2024.json"

# Loaded once at module import
with open(_BLS_WAGES_PATH, encoding="utf-8") as _fh:
    _BLS_WAGES: dict[str, dict[str, float | str | None]] = json.load(_fh)

_FALLBACK_MIN = 80_000.0
_FALLBACK_MAX = 120_000.0


def resolve_salary(
    salary_min: float | None,
    salary_max: float | None,
    canonical_role: str,
) -> tuple[float | None, float | None, bool]:
    """Resolve a salary range, filling gaps from BLS data if needed.

    Args:
        salary_min: Explicit minimum salary (or None).
        salary_max: Explicit maximum salary (or None).
        canonical_role: The canonical role name from role normalization.

    Returns:
        A tuple of (resolved_min, resolved_max, is_estimated).
        ``is_estimated`` is True when BLS data was used as a fallback.
    """
    if salary_min is not None and salary_max is not None:
        return (salary_min, salary_max, False)

    if salary_min is not None and salary_max is None:
        return (salary_min, salary_min * 1.2, False)

    if salary_min is None and salary_max is not None:
        return (salary_max * 0.8, salary_max, False)

    # Both are None — fall back to BLS data
    bls_entry = _BLS_WAGES.get(canonical_role)
    if bls_entry is not None:
        mean_wage = float(bls_entry["mean_annual_wage"])  # type: ignore[arg-type]
        return (mean_wage * 0.8, mean_wage * 1.2, True)

    # Unknown role with no BLS mapping
    return (_FALLBACK_MIN, _FALLBACK_MAX, True)
