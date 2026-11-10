"""Numerical and safety regression tests for the option premium teaching engine."""
import math

import pytest

from app.education.options_premium import (
    at_the_money_time_curve,
    expiration_profit,
    intrinsic_value,
    theoretical_option,
)


def test_exact_intrinsic_values_for_calls_and_puts():
    assert intrinsic_value(105, 100, "call") == 5
    assert intrinsic_value(95, 100, "call") == 0
    assert intrinsic_value(95, 100, "put") == 5
    assert intrinsic_value(105, 100, "put") == 0


def test_black_scholes_known_30_day_reference():
    result = theoretical_option(100, 100, 30, 30)
    assert result.premium == pytest.approx(3.4301386438779957, abs=1e-9)
    assert result.intrinsic == 0
    assert result.time_value == pytest.approx(result.premium)
    assert theoretical_option(100, 100, 30, 30, "put").premium == pytest.approx(result.premium)


def test_all_components_add_exactly_to_the_premium():
    for kind in ("call", "put"):
        for stock in (75, 90, 100, 110, 125):
            for d in (1, 30, 180):
                for vol in (10, 30, 80):
                    result = theoretical_option(stock, 100, d, vol, kind)
                    assert math.isfinite(result.premium)
                    assert result.premium >= result.intrinsic >= 0
                    assert result.time_value >= 0
                    assert result.premium == pytest.approx(result.intrinsic + result.time_value)
                    assert result.premium <= (stock if kind == "call" else 100) + 1e-9


def test_put_call_parity_with_zero_rates_and_dividends():
    for stock in (90, 100, 105, 125):
        call = theoretical_option(stock, 100, 30, 40, "call").premium
        put = theoretical_option(stock, 100, 30, 40, "put").premium
        assert call - put == pytest.approx(stock - 100, abs=1e-9)


def test_stock_direction_effect_and_volatility_impact():
    for iv in (20, 50):
        assert (
            theoretical_option(95, 100, 30, iv, "call").premium
            < theoretical_option(105, 100, 30, iv, "call").premium
        )
        assert (
            theoretical_option(95, 100, 30, iv, "put").premium
            > theoretical_option(105, 100, 30, iv, "put").premium
        )
    for kind in ("call", "put"):
        assert (
            theoretical_option(100, 100, 30, 20, kind).premium
            < theoretical_option(100, 100, 30, 50, kind).premium
        )


def test_time_value_curve_and_expiry_are_consistent():
    days = list(range(0, 181, 5))
    curve = at_the_money_time_curve(days)
    assert curve[0] == 0
    assert all(b > a for a, b in zip(curve, curve[1:]))
    for kind in ("call", "put"):
        value = theoretical_option(105, 100, 0, 40, kind)
        assert value.time_value == 0
        assert value.premium == intrinsic_value(105, 100, kind)


def test_earnings_style_volatility_crush_is_numerically_correct():
    before = theoretical_option(100, 100, 30, 60, "call").premium
    after = theoretical_option(103, 100, 29, 25, "call").premium
    assert before == pytest.approx(6.853940718253547, abs=1e-9)
    assert after == pytest.approx(4.600087256181453, abs=1e-9)
    assert before > after


def test_expiration_payoff_profit_and_breakeven():
    assert [expiration_profit(s, 100, 6) for s in (95, 104, 106, 115)] == [
        -6, -2, 0, 9,
    ]
    assert expiration_profit(95, 100, 6, "put") == -1
    assert expiration_profit(100, 100, 0) == 0


@pytest.mark.parametrize("args", [
    (-1, 100, 30, 30, "call"),
    (0, 100, 30, 30, "call"),
    (100, 0, 30, 30, "call"),
    (100, 100, -1, 30, "call"),
    (100, 100, 30, -1, "call"),
    (100, 100, 30, 30, "future"),
    (True, 100, 30, 30, "call"),
    (float("nan"), 100, 30, 30, "call"),
    (float("inf"), 100, 30, 30, "call"),
])
def test_invalid_inputs_do_not_produce_prices(args):
    with pytest.raises(ValueError):
        theoretical_option(*args)
