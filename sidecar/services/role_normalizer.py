"""Rule-based role title normalizer using a keyword taxonomy."""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"


class RoleNormalizer:
    """Normalizes job titles to canonical role names.

    Loads the role taxonomy from ``data/role_taxonomy.json`` and builds a
    keyword lookup sorted by keyword length (longest first) so that more
    specific titles match before generic ones.
    """

    def __init__(self) -> None:
        taxonomy_path = DATA_DIR / "role_taxonomy.json"
        with open(taxonomy_path, encoding="utf-8") as fh:
            taxonomy: dict[str, dict[str, list[str] | str]] = json.load(fh)

        # Build (keyword, role_name, exclude_terms) tuples sorted longest-first
        self._rules: list[tuple[str, str, list[str]]] = []
        for role_name, role_data in taxonomy.items():
            if role_name == "UNKNOWN":
                continue
            keywords: list[str] = role_data.get("keywords", [])  # type: ignore[assignment]
            exclude: list[str] = role_data.get("exclude", [])  # type: ignore[assignment]
            for kw in keywords:
                self._rules.append((kw.lower(), role_name, [e.lower() for e in exclude]))

        self._rules.sort(key=lambda r: len(r[0]), reverse=True)

    def normalize(self, title: str) -> str:
        """Map a raw job title to a canonical role name.

        Returns ``"UNKNOWN"`` if no keyword matches.
        """
        lowered = title.lower()

        for keyword, role_name, excludes in self._rules:
            if keyword in lowered:
                if excludes and any(ex in lowered for ex in excludes):
                    continue
                return role_name

        return "UNKNOWN"
