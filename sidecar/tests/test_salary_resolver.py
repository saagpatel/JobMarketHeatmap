"""Tests for salary resolution logic."""

import pytest

from services.salary_resolver import resolve_salary


def test_both_provided_passthrough() -> None:
    """When both min and max are given, return them unchanged."""
    result = resolve_salary(80000, 120000, "Software Engineer")
    assert result == (80000, 120000, False)


def test_both_provided_not_estimated() -> None:
    assert resolve_salary(100000, 200000, "UNKNOWN")[2] is False


def test_only_min_provided() -> None:
    """When only min is given, max = min * 1.2."""
    result = resolve_salary(90000, None, "Software Engineer")
    assert result == (90000, 108000.0, False)


def test_only_max_provided() -> None:
    """When only max is given, min = max * 0.8."""
    result = resolve_salary(None, 150000, "Data Scientist")
    assert result == (120000.0, 150000, False)


def test_neither_known_role_software_engineer() -> None:
    """No salary + known role → BLS estimate."""
    min_s, max_s, estimated = resolve_salary(None, None, "Software Engineer")
    assert estimated is True
    assert min_s == pytest.approx(132270 * 0.8)
    assert max_s == pytest.approx(132270 * 1.2)


def test_neither_known_role_data_scientist() -> None:
    min_s, max_s, estimated = resolve_salary(None, None, "Data Scientist")
    assert estimated is True
    assert min_s == pytest.approx(108020 * 0.8)
    assert max_s == pytest.approx(108020 * 1.2)


def test_neither_known_role_engineering_manager() -> None:
    min_s, max_s, estimated = resolve_salary(None, None, "Engineering Manager")
    assert estimated is True
    assert min_s == pytest.approx(169930 * 0.8)
    assert max_s == pytest.approx(169930 * 1.2)


def test_neither_unknown_role_fallback() -> None:
    """Unknown role with no salary → hardcoded fallback."""
    result = resolve_salary(None, None, "UNKNOWN")
    min_s, max_s, estimated = result
    assert estimated is True
    assert min_s == pytest.approx(100000 * 0.8)
    assert max_s == pytest.approx(100000 * 1.2)


def test_unknown_role_not_in_bls() -> None:
    """A role not in BLS data at all → 80k-120k fallback."""
    result = resolve_salary(None, None, "Galactic Space Pilot")
    assert result == (80000.0, 120000.0, True)


def test_zero_min_with_max() -> None:
    """Zero salary_min with a valid max."""
    result = resolve_salary(0, 100000, "Software Engineer")
    assert result == (0, 100000, False)


def test_zero_both() -> None:
    """Both zero — still passes through as explicit values."""
    result = resolve_salary(0, 0, "Software Engineer")
    assert result == (0, 0, False)


def test_only_min_float_precision() -> None:
    """Verify float math for min-only case."""
    min_s, max_s, est = resolve_salary(75000.50, None, "IT Support / SysAdmin")
    assert min_s == 75000.50
    assert max_s == pytest.approx(75000.50 * 1.2)
    assert est is False


def test_devops_bls_estimate() -> None:
    min_s, max_s, estimated = resolve_salary(None, None, "DevOps / Platform Engineer")
    assert estimated is True
    assert min_s == pytest.approx(120950 * 0.8)
    assert max_s == pytest.approx(120950 * 1.2)


def test_security_engineer_bls_estimate() -> None:
    min_s, max_s, estimated = resolve_salary(None, None, "Security Engineer")
    assert estimated is True
    assert min_s == pytest.approx(120360 * 0.8)


def test_product_manager_bls_estimate() -> None:
    min_s, max_s, estimated = resolve_salary(None, None, "Product Manager")
    assert estimated is True
    assert min_s == pytest.approx(157620 * 0.8)


def test_it_support_bls_estimate() -> None:
    min_s, max_s, estimated = resolve_salary(None, None, "IT Support / SysAdmin")
    assert estimated is True
    assert min_s == pytest.approx(91560 * 0.8)


def test_senior_software_engineer_bls_estimate() -> None:
    min_s, max_s, estimated = resolve_salary(None, None, "Senior Software Engineer")
    assert estimated is True
    assert min_s == pytest.approx(155000 * 0.8)
    assert max_s == pytest.approx(155000 * 1.2)


def test_data_engineer_bls_estimate() -> None:
    min_s, max_s, estimated = resolve_salary(None, None, "Data Engineer")
    assert estimated is True
    assert min_s == pytest.approx(132270 * 0.8)
