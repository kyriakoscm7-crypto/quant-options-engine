"""Tests for ETF education models."""

import pytest

from app.education.etf_models import (
    EXAMPLE_FUNDS,
    annual_fee_cost,
    concentration_index,
    fund_overlap,
    portfolio_exposure,
)


def test_example_funds_sum_to_100():
    for holdings in EXAMPLE_FUNDS.values():
        assert sum(holdings.values()) == pytest.approx(100)


def test_overlapping_funds():
    overlap = fund_overlap(
        EXAMPLE_FUNDS["Broad Market"],
        EXAMPLE_FUNDS["Technology Focus"],
    )
    assert overlap == pytest.approx(45)


def test_identical_funds_have_full_overlap():
    fund = EXAMPLE_FUNDS["Broad Market"]
    assert fund_overlap(fund, fund) == pytest.approx(100)


def test_disjoint_funds_have_zero_overlap():
    assert fund_overlap({"A": 100}, {"B": 100}) == 0


def test_portfolio_exposure():
    result = portfolio_exposure(
        {
            "Broad": EXAMPLE_FUNDS["Broad Market"],
            "Tech": EXAMPLE_FUNDS["Technology Focus"],
        },
        {"Broad": 50, "Tech": 50},
    )
    assert result["Company A"] == pytest.approx(35)
    assert sum(result.values()) == pytest.approx(100)


def test_single_holding_has_max_concentration():
    assert concentration_index({"Company A": 100}) == pytest.approx(1)


def test_equal_holdings_are_less_concentrated():
    assert concentration_index(
        {"A": 50, "B": 50}
    ) == pytest.approx(0.5)


def test_annual_fee_cost():
    assert annual_fee_cost(10000, 0.25) == pytest.approx(25)


@pytest.mark.parametrize("value,fee", [
    (-100, 0.25),
    (10000, -1),
    (10000, 101),
    (float("nan"), 0.5),
])
def test_invalid_fee_inputs(value, fee):
    with pytest.raises(ValueError):
        annual_fee_cost(value, fee)


def test_invalid_fund_weights():
    with pytest.raises(ValueError):
        fund_overlap({"A": 60}, {"B": 100})


def test_invalid_portfolio_allocations():
    with pytest.raises(ValueError):
        portfolio_exposure(
            {"Broad": EXAMPLE_FUNDS["Broad Market"]},
            {"Broad": 50},
        )
