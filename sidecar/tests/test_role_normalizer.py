"""Tests for role title normalizer."""

import pytest

from services.role_normalizer import RoleNormalizer


@pytest.fixture(scope="module")
def normalizer() -> RoleNormalizer:
    return RoleNormalizer()


def test_software_engineer(normalizer: RoleNormalizer) -> None:
    assert normalizer.normalize("Software Engineer") == "Software Engineer"


def test_senior_software_engineer(normalizer: RoleNormalizer) -> None:
    assert normalizer.normalize("Senior Software Engineer") == "Senior Software Engineer"


def test_senior_devops_engineer(normalizer: RoleNormalizer) -> None:
    assert normalizer.normalize("Senior DevOps Engineer") == "DevOps / Platform Engineer"


def test_site_reliability_engineer(normalizer: RoleNormalizer) -> None:
    assert normalizer.normalize("Site Reliability Engineer") == "DevOps / Platform Engineer"


def test_vp_of_engineering(normalizer: RoleNormalizer) -> None:
    assert normalizer.normalize("VP of Engineering") == "Engineering Manager"


def test_junior_data_scientist(normalizer: RoleNormalizer) -> None:
    assert normalizer.normalize("Junior Data Scientist") == "Data Scientist"


def test_full_stack_engineer(normalizer: RoleNormalizer) -> None:
    assert normalizer.normalize("Full Stack Engineer") == "Software Engineer"


def test_unknown_title(normalizer: RoleNormalizer) -> None:
    assert normalizer.normalize("Random Job Title") == "UNKNOWN"


def test_case_insensitive_ml_engineer(normalizer: RoleNormalizer) -> None:
    assert normalizer.normalize("machine learning engineer") == "Data Scientist"


def test_lead_software_engineer(normalizer: RoleNormalizer) -> None:
    assert normalizer.normalize("Lead Software Engineer") == "Senior Software Engineer"


def test_staff_engineer(normalizer: RoleNormalizer) -> None:
    assert normalizer.normalize("Staff Engineer") == "Senior Software Engineer"


def test_it_support_specialist(normalizer: RoleNormalizer) -> None:
    assert normalizer.normalize("IT Support Specialist") == "IT Support / SysAdmin"


def test_product_owner(normalizer: RoleNormalizer) -> None:
    assert normalizer.normalize("Product Owner") == "Product Manager"


def test_empty_string(normalizer: RoleNormalizer) -> None:
    assert normalizer.normalize("") == "UNKNOWN"


def test_penetration_tester(normalizer: RoleNormalizer) -> None:
    assert normalizer.normalize("Penetration Tester") == "Security Engineer"


def test_backend_engineer_no_senior(normalizer: RoleNormalizer) -> None:
    """Backend engineer without 'senior' maps to Software Engineer."""
    assert normalizer.normalize("Backend Engineer") == "Software Engineer"


def test_principal_engineer(normalizer: RoleNormalizer) -> None:
    assert normalizer.normalize("Principal Engineer") == "Senior Software Engineer"


def test_data_engineer(normalizer: RoleNormalizer) -> None:
    assert normalizer.normalize("Data Engineer") == "Data Engineer"


def test_cloud_engineer(normalizer: RoleNormalizer) -> None:
    assert normalizer.normalize("Cloud Engineer") == "DevOps / Platform Engineer"


def test_cybersecurity_engineer(normalizer: RoleNormalizer) -> None:
    assert normalizer.normalize("Cybersecurity Engineer") == "Security Engineer"


def test_network_administrator(normalizer: RoleNormalizer) -> None:
    assert normalizer.normalize("Network Administrator") == "IT Support / SysAdmin"


def test_director_of_engineering(normalizer: RoleNormalizer) -> None:
    assert normalizer.normalize("Director of Engineering") == "Engineering Manager"


def test_technical_product_manager(normalizer: RoleNormalizer) -> None:
    assert normalizer.normalize("Technical Product Manager") == "Product Manager"
