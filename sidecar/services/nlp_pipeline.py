"""NLP pipeline for skill extraction using spaCy and ESCO skill patterns."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path

import spacy
from spacy.language import Language

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"


@dataclass
class SkillMatch:
    """A skill extracted from text."""

    skill_raw: str
    skill_norm: str
    confidence: float = 1.0


def _load_esco_patterns() -> list[dict[str, str]]:
    """Load ESCO skills and build SpanRuler patterns."""
    esco_path = DATA_DIR / "esco_skills_subset.json"
    with open(esco_path, encoding="utf-8") as fh:
        skills: list[dict[str, list[str] | str]] = json.load(fh)

    patterns: list[dict[str, str]] = []
    for entry in skills:
        preferred: str = entry["preferred_label"]  # type: ignore[assignment]
        alt_labels: list[str] = entry.get("alt_labels", [])  # type: ignore[assignment]

        all_labels = [preferred, *alt_labels]
        for label in all_labels:
            patterns.append({"label": "SKILL", "pattern": label, "id": preferred})

    return patterns


class NlpPipeline:
    """spaCy pipeline with ESCO skill span ruler for skill extraction."""

    def __init__(self) -> None:
        self._nlp: Language = spacy.load(
            "en_core_web_sm", disable=["ner", "parser", "lemmatizer"]
        )

        patterns = _load_esco_patterns()

        ruler = self._nlp.add_pipe(
            "span_ruler",
            config={
                "spans_key": "ruler",
                "phrase_matcher_attr": "LOWER",
            },
        )
        ruler.add_patterns(patterns)  # type: ignore[union-attr]

        logger.info("NLP pipeline loaded with %d skill patterns", len(patterns))

    def extract_skills(self, text: str) -> list[SkillMatch]:
        """Extract deduplicated skills from text.

        Returns a list of :class:`SkillMatch` with normalized skill names.
        Duplicates (by ``skill_norm``) are removed, keeping the first occurrence.
        """
        doc = self._nlp(text)
        spans = doc.spans.get("ruler", [])

        seen: set[str] = set()
        results: list[SkillMatch] = []

        for span in spans:
            skill_id: str = span.id_
            if skill_id in seen:
                continue
            seen.add(skill_id)
            results.append(
                SkillMatch(
                    skill_raw=span.text,
                    skill_norm=skill_id,
                )
            )

        return results


# Module-level singleton
_pipeline: NlpPipeline | None = None


def get_pipeline() -> NlpPipeline:
    """Return the singleton NLP pipeline, creating it on first call."""
    global _pipeline  # noqa: PLW0603
    if _pipeline is None:
        _pipeline = NlpPipeline()
    return _pipeline
