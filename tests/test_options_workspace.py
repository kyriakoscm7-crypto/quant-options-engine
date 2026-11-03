"""Regression tests for the Options Research Workspace model."""

import pytest

from app.pricing.options_workspace import (
    breakeven,
    expiration_profit,
    scenario_mark_profit,
    theoretical_price,
)


def test_long_call_breakeven():
    assert breakeven("Call", 100, 5) == 105


def test_long_put_breakeven():
    assert breakeven("Put", 100, 5) == 95


def test_call_expiration_profit():
    assert expiration_profit("Call", 100, 5, 110) == pytest.approx(500)


def test_put_expiration_profit():
    assert expiration_profit("Put", 100, 5, 90) == pytest.approx(500)


def test_long_option_maximum_loss():
    assert expiration_profit("Call", 100, 5, 80, 2) == -1000
    assert expiration_profit("Put", 100, 5, 120, 2) == -1000


def test_model_mark_is_zero_pnl_at_identical_state():
    premium = theoretical_price("Call", 100, 100, 30, 25)
    pnl = scenario_mark_profit(
        "Call", 100, 100, 30, 25, premium
    )
    assert pnl == pytest.approx(0, abs=1e-9)


def test_invalid_market_inputs():
    with pytest.raises(ValueError):
        theoretical_price("Call", 100, 100, 0, 25)
    with pytest.raises(ValueError):
        theoretical_price("Call", 100, 100, 30, 0)


def test_call_and_put_prices_positive():
    call = theoretical_price("Call", 100, 100, 30, 25)
    put = theoretical_price("Put", 100, 100, 30, 25)
    assert call > 0
    assert put > 0
