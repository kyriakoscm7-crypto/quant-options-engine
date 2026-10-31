"""Tests for the simplified Canadian account comparison."""

import pytest

from app.education.account_comparison import compare_accounts


def test_equal_tax_rates_produce_equal_after_tax_results():
    result = compare_accounts(5000, 30, 30, 5, 20)
    assert result.rrsp_after_tax_value == pytest.approx(
        result.tfsa_future_value
    )


def test_lower_future_tax_rate_favours_rrsp_in_this_model():
    result = compare_accounts(5000, 35, 20, 5, 20)
    assert result.difference > 0


def test_higher_future_tax_rate_favours_tfsa_in_this_model():
    result = compare_accounts(5000, 20, 35, 5, 20)
    assert result.difference < 0


def test_rrsp_deduction_is_financed_consistently():
    result = compare_accounts(7000, 30, 20, 0, 0)
    assert result.rrsp_contribution == pytest.approx(10000)
    assert result.rrsp_deduction_value == pytest.approx(3000)
    assert result.rrsp_contribution - result.rrsp_deduction_value == pytest.approx(7000)


def test_zero_tax_rates_equal_balances():
    result = compare_accounts(5000, 0, 0, 0, 10)
    assert result.tfsa_future_value == pytest.approx(5000)
    assert result.rrsp_after_tax_value == pytest.approx(5000)


def test_negative_returns_supported():
    result = compare_accounts(1000, 30, 30, -5, 10)
    assert result.tfsa_future_value < 1000
    assert result.difference == pytest.approx(0)


@pytest.mark.parametrize("args", [
    (-100, 30, 20, 5, 10),
    (1000, 100, 20, 5, 10),
    (1000, 30, -5, 5, 10),
    (1000, 30, 20, -100, 10),
    (1000, 30, 20, 5, -1),
    (1000, 30, 20, 5, 81),
    (1000, 30, 20, 5, 1.5),
    (float("nan"), 30, 20, 5, 10),
])
def test_invalid_inputs_rejected(args):
    with pytest.raises(ValueError):
        compare_accounts(*args)
