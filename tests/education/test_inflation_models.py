"""Tests for inflation education models."""

import pytest

from app.education.inflation_models import (
    purchasing_power,
    real_return_pct,
)


def test_zero_inflation():
    r = purchasing_power(100, 1000, 0, 0, 10)
    assert r.future_price == pytest.approx(100)
    assert r.savings_in_today_dollars == pytest.approx(1000)


def test_prices_increase_with_inflation():
    r = purchasing_power(100, 1000, 3, 0, 10)
    assert r.future_price > 100
    assert r.savings_in_today_dollars < 1000


def test_equal_inflation_and_return_preserve_purchasing_power():
    r = purchasing_power(100, 1000, 4, 4, 20)
    assert r.savings_in_today_dollars == pytest.approx(1000)
    assert r.purchasing_power_change_pct == pytest.approx(0)


def test_return_below_inflation_loses_purchasing_power():
    r = purchasing_power(100, 1000, 4, 2, 20)
    assert r.future_savings > 1000
    assert r.savings_in_today_dollars < 1000


def test_exact_real_return():
    assert real_return_pct(5, 3) == pytest.approx(
        ((1.05 / 1.03) - 1) * 100
    )


def test_negative_inflation_supported():
    r = purchasing_power(100, 1000, -2, 0, 5)
    assert r.future_price < 100


def test_zero_years():
    r = purchasing_power(100, 1000, 3, 5, 0)
    assert r.future_price == 100
    assert r.future_savings == 1000


@pytest.mark.parametrize("args", [
    (-100, 1000, 3, 5, 10),
    (100, -1000, 3, 5, 10),
    (100, 1000, -100, 5, 10),
    (100, 1000, 3, -100, 10),
    (100, 1000, 3, 5, -1),
    (100, 1000, 3, 5, 101),
    (100, 1000, 3, 5, 1.5),
    (float("nan"), 1000, 3, 5, 10),
])
def test_invalid_inputs(args):
    with pytest.raises(ValueError):
        purchasing_power(*args)
