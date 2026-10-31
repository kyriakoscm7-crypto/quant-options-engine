
import pytest

from app.education.financial_models import (
    compound_growth,
    credit_card_payoff,
)


def test_growth_with_no_return():
    result = compound_growth(1000, 100, 0, 2)
    assert len(result) == 3
    assert result[-1].balance == pytest.approx(3400)
    assert result[-1].growth == pytest.approx(0)


def test_compounding_increases_balance():
    result = compound_growth(1000, 100, 6, 10)
    assert result[-1].balance > result[-1].contributed
    assert result[-1].year == 10


def test_growth_supports_zero_years():
    result = compound_growth(500, 50, 5, 0)
    assert len(result) == 1
    assert result[0].balance == 500


@pytest.mark.parametrize("amount,monthly,rate,years", [
    (-100, 50, 5, 10),
    (100, -50, 5, 10),
    (100, 50, -100, 10),
    (100, 50, 5, -1),
])
def test_growth_rejects_invalid_inputs(amount, monthly, rate, years):
    with pytest.raises(ValueError):
        compound_growth(amount, monthly, rate, years)


def test_zero_interest_credit_card():
    result = credit_card_payoff(1000, 0, 100)
    assert result.months == 10
    assert result.interest_paid == pytest.approx(0)
    assert result.total_paid == pytest.approx(1000)


def test_interest_increases_debt_cost():
    result = credit_card_payoff(1000, 12, 100)
    assert result.months > 10
    assert result.interest_paid > 0
    assert result.total_paid > 1000


def test_payment_must_cover_interest():
    with pytest.raises(ValueError):
        credit_card_payoff(1000, 24, 10)


def test_zero_balance_needs_no_payments():
    result = credit_card_payoff(0, 20, 0)
    assert result.months == 0
    assert result.total_paid == 0
