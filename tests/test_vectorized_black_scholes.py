"""
Tests for the vectorized Black-Scholes-Merton pricing engine.

Verify that batch pricing matches the original scalar engine,
including dividends, expiration, zero volatility, and invalid inputs.
"""

import numpy as np
import pytest

from app.pricing.black_scholes import BlackScholes
from app.pricing.vectorized_black_scholes import price_options_vectorized


@pytest.mark.parametrize(
    ("S", "K", "T", "r", "sigma", "q"),
    [
        (100, 100, 1.0, 0.05, 0.20, 0.0),
        (100, 90, 0.5, 0.045, 0.25, 0.01),
        (100, 110, 2.0, 0.03, 0.30, 0.02),
        (150, 100, 0.25, 0.04, 0.15, 0.0),
        (80, 100, 1.5, 0.02, 0.40, 0.03),
        (100, 100, 0.0, 0.05, 0.20, 0.0),
        (100, 90, 0.0, 0.05, 0.20, 0.0),
        (90, 100, 0.0, 0.05, 0.20, 0.0),
        (100, 100, 1.0, 0.05, 0.0, 0.0),
        (100, 90, 1.0, 0.05, 0.0, 0.02),
        (90, 100, 1.0, 0.05, 0.0, 0.02),
        (100, 100, 1.0, -0.01, 0.20, 0.01),
    ],
)
def test_vectorized_matches_original(S, K, T, r, sigma, q):
    """Vectorized prices must match the original pricing engine."""

    original = BlackScholes(S, K, T, r, sigma, q)

    calls, puts = price_options_vectorized(S, K, T, r, sigma, q)

    assert float(calls) == pytest.approx(
        original.call_price(), abs=1e-10
    )
    assert float(puts) == pytest.approx(
        original.put_price(), abs=1e-10
    )


def test_vectorized_multiple_options():
    """Price several contracts in one batch."""

    strikes = np.array([80, 90, 100, 110, 120], dtype=float)

    calls, puts = price_options_vectorized(
        S=100,
        K=strikes,
        T=1.0,
        r=0.045,
        sigma=0.20,
        q=0.01,
    )

    assert calls.shape == (5,)
    assert puts.shape == (5,)

    for index, strike in enumerate(strikes):
        original = BlackScholes(
            100, strike, 1.0, 0.045, 0.20, 0.01
        )

        assert calls[index] == pytest.approx(
            original.call_price(), abs=1e-10
        )
        assert puts[index] == pytest.approx(
            original.put_price(), abs=1e-10
        )


def test_vectorized_mixed_expiration_and_volatility():
    """One batch can contain standard, expired, and zero-vol options."""

    stocks = np.array([100, 100, 100, 90, 110])
    strikes = np.array([100, 90, 110, 100, 100])
    times = np.array([1.0, 0.0, 0.0, 1.0, 0.5])
    volatilities = np.array([0.20, 0.20, 0.20, 0.0, 0.0])

    calls, puts = price_options_vectorized(
        stocks, strikes, times, 0.05, volatilities
    )

    for index in range(len(stocks)):
        original = BlackScholes(
            stocks[index],
            strikes[index],
            times[index],
            0.05,
            volatilities[index],
        )

        assert calls[index] == pytest.approx(
            original.call_price(), abs=1e-10
        )
        assert puts[index] == pytest.approx(
            original.put_price(), abs=1e-10
        )


def test_vectorized_put_call_parity():
    """European option prices must satisfy put-call parity."""

    S = np.array([90.0, 100.0, 110.0])
    K = np.array([100.0, 100.0, 100.0])
    T = np.array([0.25, 0.5, 1.0])
    r = 0.045
    q = 0.02

    calls, puts = price_options_vectorized(
        S, K, T, r, 0.25, q
    )

    expected = S * np.exp(-q * T) - K * np.exp(-r * T)

    np.testing.assert_allclose(
        calls - puts, expected, atol=1e-10
    )


def test_vectorized_large_batch():
    """Verify correctness and output size for 10,000 contracts."""

    strikes = np.linspace(50, 150, 10_000)

    calls, puts = price_options_vectorized(
        100, strikes, 0.5, 0.045, 0.20
    )

    assert calls.shape == (10_000,)
    assert puts.shape == (10_000,)
    assert np.all(np.isfinite(calls))
    assert np.all(np.isfinite(puts))
    assert np.all(calls >= 0)
    assert np.all(puts >= 0)


def test_vectorized_broadcasting():
    """Inputs with compatible shapes should broadcast correctly."""

    stocks = np.array([[90.0], [100.0], [110.0]])
    strikes = np.array([[90.0, 100.0, 110.0]])

    calls, puts = price_options_vectorized(
        stocks, strikes, 1.0, 0.05, 0.20
    )

    assert calls.shape == (3, 3)
    assert puts.shape == (3, 3)


def test_vectorized_empty_arrays():
    """Empty input arrays should produce empty output arrays."""

    calls, puts = price_options_vectorized(
        100, np.array([]), 1.0, 0.05, 0.20
    )

    assert calls.size == 0
    assert puts.size == 0


@pytest.mark.parametrize(
    ("parameter", "invalid_value", "error_message"),
    [
        ("S", 0.0, "Stock price"),
        ("S", -100.0, "Stock price"),
        ("K", 0.0, "Strike price"),
        ("K", -100.0, "Strike price"),
        ("T", -1.0, "Time to expiration"),
        ("sigma", -0.20, "Volatility"),
        ("S", np.nan, "finite"),
        ("K", np.inf, "finite"),
        ("T", -np.inf, "finite"),
        ("r", np.nan, "finite"),
        ("sigma", np.inf, "finite"),
        ("q", np.nan, "finite"),
    ],
)
def test_vectorized_invalid_parameters(
    parameter, invalid_value, error_message
):
    """Invalid financial inputs should raise clear errors."""

    inputs = {
        "S": 100.0,
        "K": 100.0,
        "T": 1.0,
        "r": 0.05,
        "sigma": 0.20,
        "q": 0.0,
    }

    inputs[parameter] = invalid_value

    with pytest.raises(ValueError, match=error_message):
        price_options_vectorized(**inputs)


def test_vectorized_rejects_invalid_array_element():
    """One invalid value should cause the entire batch to fail."""

    with pytest.raises(ValueError, match="Stock price"):
        price_options_vectorized(
            S=[100.0, -50.0, 120.0],
            K=100.0,
            T=1.0,
            r=0.05,
            sigma=0.20,
        )


def test_vectorized_rejects_incompatible_shapes():
    """Arrays that cannot broadcast should raise ValueError."""

    with pytest.raises(ValueError):
        price_options_vectorized(
            S=[90.0, 100.0],
            K=[90.0, 100.0, 110.0],
            T=1.0,
            r=0.05,
            sigma=0.20,
        )