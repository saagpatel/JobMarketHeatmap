"""Tests for the NLP skill extraction pipeline."""

from services.nlp_pipeline import NlpPipeline, SkillMatch


def _skill_norms(results: list[SkillMatch]) -> set[str]:
    """Extract the normalized skill names as a set."""
    return {m.skill_norm for m in results}


def test_python_and_kubernetes(nlp: NlpPipeline) -> None:
    """Extracts multiple skills from a typical sentence."""
    results = nlp.extract_skills(
        "Python developer with Kubernetes experience"
    )
    norms = _skill_norms(results)
    assert "Python" in norms
    assert "Kubernetes" in norms


def test_react_and_typescript(nlp: NlpPipeline) -> None:
    results = nlp.extract_skills(
        "Looking for a React and TypeScript engineer"
    )
    norms = _skill_norms(results)
    assert "React" in norms
    assert "TypeScript" in norms


def test_multiple_skills_aws_docker_cicd(nlp: NlpPipeline) -> None:
    results = nlp.extract_skills(
        "Experience with AWS, Docker, and CI/CD"
    )
    norms = _skill_norms(results)
    assert "Amazon Web Services" in norms
    assert "Docker" in norms
    assert "Continuous integration" in norms


def test_empty_string(nlp: NlpPipeline) -> None:
    results = nlp.extract_skills("")
    assert results == []


def test_no_relevant_skills(nlp: NlpPipeline) -> None:
    results = nlp.extract_skills("No relevant skills here at all")
    assert results == []


def test_single_skill(nlp: NlpPipeline) -> None:
    results = nlp.extract_skills("Must know PostgreSQL")
    norms = _skill_norms(results)
    assert "PostgreSQL" in norms


def test_duplicate_mention_deduplicated(nlp: NlpPipeline) -> None:
    """Repeated mentions of the same skill produce one result."""
    results = nlp.extract_skills(
        "Python experience required. Strong Python skills needed. Python Python Python."
    )
    python_matches = [m for m in results if m.skill_norm == "Python"]
    assert len(python_matches) == 1


def test_case_insensitive_python(nlp: NlpPipeline) -> None:
    """Lowercase 'python' still matches."""
    results = nlp.extract_skills("experience with python programming")
    norms = _skill_norms(results)
    assert "Python" in norms


def test_alt_label_k8s(nlp: NlpPipeline) -> None:
    """Alt label 'K8s' maps to normalized 'Kubernetes'."""
    results = nlp.extract_skills("Deploy services on K8s clusters")
    norms = _skill_norms(results)
    assert "Kubernetes" in norms


def test_long_job_description(nlp: NlpPipeline) -> None:
    """Realistic job description extracts many skills."""
    desc = (
        "We are seeking a senior backend engineer proficient in Python, "
        "Go, and Java. The ideal candidate has experience with Kubernetes, "
        "Docker, Terraform, and AWS. Familiarity with PostgreSQL, Redis, "
        "and Kafka is a plus. Our team uses Agile methodology with CI/CD "
        "pipelines and monitors with Grafana and Prometheus."
    )
    results = nlp.extract_skills(desc)
    norms = _skill_norms(results)
    assert len(norms) >= 8
    assert "Python" in norms
    assert "Docker" in norms
    assert "Kubernetes" in norms


def test_skill_match_has_confidence(nlp: NlpPipeline) -> None:
    """SkillMatch objects have a default confidence of 1.0."""
    results = nlp.extract_skills("Experience with Docker")
    assert len(results) >= 1
    assert results[0].confidence == 1.0


def test_skill_match_raw_text(nlp: NlpPipeline) -> None:
    """skill_raw preserves the original text span."""
    results = nlp.extract_skills("Proficient in React.js")
    react_matches = [m for m in results if m.skill_norm == "React"]
    assert len(react_matches) == 1
    assert react_matches[0].skill_raw == "React.js"


def test_multiple_alt_labels(nlp: NlpPipeline) -> None:
    """Different alt labels for the same skill map to the same norm."""
    results_a = nlp.extract_skills("Uses ReactJS extensively")
    results_b = nlp.extract_skills("Uses React.js extensively")
    assert _skill_norms(results_a) == _skill_norms(results_b)


def test_non_tech_text(nlp: NlpPipeline) -> None:
    """Random non-tech text yields no skills."""
    results = nlp.extract_skills(
        "The quick brown fox jumps over the lazy dog near the river bank"
    )
    assert results == []


def test_returns_list_of_skill_match(nlp: NlpPipeline) -> None:
    """Return type is a list of SkillMatch dataclass instances."""
    results = nlp.extract_skills("Python")
    assert isinstance(results, list)
    if results:
        assert isinstance(results[0], SkillMatch)
