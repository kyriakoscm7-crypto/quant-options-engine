"""Tests for Greeks Risk Intelligence calculations."""

import pytest

from app.pricing.greeks_workspace import calculate_greeks, compare_repricing


def test_call_and_put_delta_sign():
    call = calculate_greeks("Call", 100, 100, 30, 25)
    put = calculate_greeks("Put", 100, 100, 30, 25)
    assert call["delta"] > 0
    assert put["delta"] < 0


def test_gamma_and_vega_positive():
    result = calculate_greeks("Call", 100, 100, 30, 25)
    assert result["gamma"] > 0
    assert result["vega"] > 0


def test_theta_per_calendar_day():
    result = calculate_greeks("Call", 100, 100, 30, 25)
    assert -1 < result["theta"] < 0


def test_zero_move_identity():
    result = compare_repricing("Call", 100, 100, 30, 25, 0)
    assert result["approx_price"] == pytest.approx(
        result["full_price"]
    )


def test_small_move_approximation():
    result = compare_repricing("Call", 100, 100, 30, 25, 0.1)
    assert abs(result["approx_error"]) < 0.01


def test_invalid_option():
    with pytest.raises(ValueError):
        calculate_greeks("Other", 100, 100, 30, 25)


def test_invalid_expiration():
    with pytest.raises(ValueError):
        calculate_greeks("Call", 100, 100, 0, 25)


def test_invalid_scenario():
    with pytest.raises(ValueError):
        compare_repricing("Call", 100, 100, 30, 25, -100)
