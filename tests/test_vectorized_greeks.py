"""
Automated tests for vectorized Black-Scholes-Merton Greeks.

These tests verify that:

1. Vectorized Greeks match the original scalar engine.
2. All expected result arrays are returned.
3. NumPy broadcasting works correctly.
4. Dividend yields are handled correctly.
5. Expired and zero-volatility contracts are handled safely.
6. Invalid financial parameters are rejected.
7. The original vectorized pricing engine remains consistent.

Run:

    python -m pytest tests/test_vectorized_greeks.py -v
"""

import numpy as np
import pytest

from app.pricing.black_scholes import BlackScholes
from app.pricing.vectorized_black_scholes import (
    greeks_options_vectorized,
    price_options_vectorized,
)

# ============================================================
# EXPECTED OUTPUT FIELDS
# ============================================================

EXPECTED_FIELDS = (
    "call_price",
    "put_price",
    "call_delta",
    "put_delta",
    "gamma",
    "vega",
    "call_theta",
    "put_theta",
    "call_rho",
    "put_rho",
)


# ============================================================
# BASIC FUNCTIONALITY
# ============================================================

def test_returns_all_expected_fields():
    """Verify that all option prices and Greeks are returned."""

    results = greeks_options_vectorized(
        S=100,
        K=100,
        T=1,
        r=0.05,
        sigma=0.2,
    )

    assert set(results) == set(EXPECTED_FIELDS)


def test_all_outputs_are_numpy_arrays():
    """Verify that every output is a NumPy array."""

    results = greeks_options_vectorized(
        S=100,
        K=[90, 100, 110],
        T=1,
        r=0.05,
        sigma=0.2,
    )

    for name in EXPECTED_FIELDS:
        assert isinstance(results[name], np.ndarray)


def test_output_shapes_match_broadcast_inputs():
    """Verify that output arrays preserve the broadcast shape."""

    results = greeks_options_vectorized(
        S=100,
        K=[90, 100, 110],
        T=1,
        r=0.05,
        sigma=0.2,
    )

    for name in EXPECTED_FIELDS:
        assert results[name].shape == (3,)


# ============================================================
# COMPARISON AGAINST ORIGINAL BLACK-SCHOLES ENGINE
# ============================================================

@pytest.mark.parametrize(
    ("S", "K", "T", "r", "sigma", "q"),
    [
        (100, 100, 1.0, 0.05, 0.20, 0.00),
        (100, 90, 0.5, 0.03, 0.25, 0.01),
        (100, 110, 2.0, 0.04, 0.30, 0.02),
        (50, 60, 0.25, 0.02, 0.40, 0.00),
        (200, 180, 1.5, 0.06, 0.15, 0.03),
        (100, 100, 0.1, -0.01, 0.35, 0.00),
        (150, 125, 3.0, 0.07, 0.50, 0.04),
        (80, 95, 0.75, 0.00, 0.22, 0.015),
        (120, 120, 0.02, 0.05, 0.60, 0.01),
        (100, 105, 5.0, 0.03, 0.18, 0.025),
    ],
)
def test_matches_scalar_black_scholes(
    S,
    K,
    T,
    r,
    sigma,
    q,
):
    """Verify numerical agreement with the original engine."""

    scalar = BlackScholes(
        S=S,
        K=K,
        T=T,
        r=r,
        sigma=sigma,
        q=q,
    ).greeks()

    vectorized = greeks_options_vectorized(
        S=S,
        K=K,
        T=T,
        r=r,
        sigma=sigma,
        q=q,
    )

    for name in EXPECTED_FIELDS:

        # The scalar engine rounds every output to four decimals.
        # Apply the same rounding before comparing.
        actual = round(float(vectorized[name]), 4)

        assert actual == pytest.approx(
            scalar[name],
            abs=1e-4,
        )


# ============================================================
# NUMPY BROADCASTING
# ============================================================

def test_multiple_strikes():
    """Verify pricing across multiple strike prices."""

    strikes = np.array([80, 90, 100, 110, 120])

    results = greeks_options_vectorized(
        S=100,
        K=strikes,
        T=1,
        r=0.05,
        sigma=0.2,
    )

    assert results["call_price"].shape == (5,)

    # Call prices generally decrease as strike increases.
    assert np.all(np.diff(results["call_price"]) < 0)


def test_multiple_expirations():
    """Verify support for multiple expiration times."""

    results = greeks_options_vectorized(
        S=100,
        K=100,
        T=[0.1, 0.5, 1.0, 2.0],
        r=0.05,
        sigma=0.2,
    )

    assert results["gamma"].shape == (4,)

    assert np.all(np.isfinite(results["gamma"]))


def test_multiple_volatilities():
    """Verify support for multiple volatility values."""

    results = greeks_options_vectorized(
        S=100,
        K=100,
        T=1,
        r=0.05,
        sigma=[0.1, 0.2, 0.3, 0.4],
    )

    assert results["vega"].shape == (4,)


def test_two_dimensional_broadcasting():
    """Verify that multidimensional broadcasting works."""

    strikes = np.array([[90], [100], [110]])

    volatilities = np.array([[0.15, 0.20, 0.25]])

    results = greeks_options_vectorized(
        S=100,
        K=strikes,
        T=1,
        r=0.05,
        sigma=volatilities,
    )

    for name in EXPECTED_FIELDS:
        assert results[name].shape == (3, 3)


# ============================================================
# FINANCIAL PROPERTIES
# ============================================================

def test_call_delta_is_positive():
    """European call delta should be positive."""

    results = greeks_options_vectorized(
        S=100,
        K=[90, 100, 110],
        T=1,
        r=0.05,
        sigma=0.2,
    )

    assert np.all(results["call_delta"] > 0)


def test_put_delta_is_negative():
    """European put delta should be negative."""

    results = greeks_options_vectorized(
        S=100,
        K=[90, 100, 110],
        T=1,
        r=0.05,
        sigma=0.2,
    )

    assert np.all(results["put_delta"] < 0)


def test_gamma_is_positive():
    """Standard Black-Scholes gamma should be positive."""

    results = greeks_options_vectorized(
        S=100,
        K=100,
        T=1,
        r=0.05,
        sigma=0.2,
    )

    assert float(results["gamma"]) > 0


def test_vega_is_positive():
    """Standard Black-Scholes vega should be positive."""

    results = greeks_options_vectorized(
        S=100,
        K=100,
        T=1,
        r=0.05,
        sigma=0.2,
    )

    assert float(results["vega"]) > 0


def test_call_rho_is_positive():
    """European call rho should be positive."""

    results = greeks_options_vectorized(
        S=100,
        K=100,
        T=1,
        r=0.05,
        sigma=0.2,
    )

    assert float(results["call_rho"]) > 0


def test_put_rho_is_negative():
    """European put rho should be negative."""

    results = greeks_options_vectorized(
        S=100,
        K=100,
        T=1,
        r=0.05,
        sigma=0.2,
    )

    assert float(results["put_rho"]) < 0


def test_delta_difference_equals_dividend_discount():
    """Call delta minus put delta should equal exp(-qT)."""

    time = 1.5
    dividend = 0.03

    results = greeks_options_vectorized(
        S=100,
        K=100,
        T=time,
        r=0.05,
        sigma=0.2,
        q=dividend,
    )

    difference = (
        float(results["call_delta"])
        - float(results["put_delta"])
    )

    expected = np.exp(-dividend * time)

    assert difference == pytest.approx(expected)


# ============================================================
# EDGE CASES
# ============================================================

def test_expired_option_has_undefined_greeks():
    """Expired contracts should have NaN Greeks."""

    results = greeks_options_vectorized(
        S=110,
        K=100,
        T=0,
        r=0.05,
        sigma=0.2,
    )

    assert float(results["call_price"]) == 10.0
    assert float(results["put_price"]) == 0.0

    for name in EXPECTED_FIELDS[2:]:
        assert np.isnan(results[name])


def test_zero_volatility_has_undefined_greeks():
    """Zero-volatility contracts should have NaN Greeks."""

    results = greeks_options_vectorized(
        S=100,
        K=100,
        T=1,
        r=0.05,
        sigma=0,
    )

    assert np.isfinite(results["call_price"])
    assert np.isfinite(results["put_price"])

    for name in EXPECTED_FIELDS[2:]:
        assert np.isnan(results[name])


def test_mixed_valid_and_invalid_greek_cases():
    """Verify that valid contracts retain their Greeks."""

    results = greeks_options_vectorized(
        S=[100, 100, 100],
        K=100,
        T=[1, 0, 1],
        r=0.05,
        sigma=[0.2, 0.2, 0],
    )

    assert np.isfinite(results["call_delta"][0])

    assert np.isnan(results["call_delta"][1])
    assert np.isnan(results["call_delta"][2])

    assert np.all(np.isfinite(results["call_price"]))
    assert np.all(np.isfinite(results["put_price"]))


def test_all_contracts_have_undefined_greeks():
    """Verify handling when no contracts have valid analytical Greeks."""

    results = greeks_options_vectorized(
        S=[100, 110],
        K=100,
        T=[0, 1],
        r=0.05,
        sigma=[0.2, 0],
    )

    assert np.all(np.isnan(results["gamma"]))


# ============================================================
# INPUT VALIDATION
# ============================================================

@pytest.mark.parametrize(
    ("parameter", "value"),
    [
        ("S", 0),
        ("S", -100),
        ("K", 0),
        ("K", -100),
        ("T", -1),
        ("sigma", -0.2),
        ("S", np.nan),
        ("K", np.inf),
        ("T", -np.inf),
        ("r", np.nan),
        ("sigma", np.inf),
        ("q", np.nan),
    ],
)
def test_invalid_inputs_are_rejected(parameter, value):
    """Verify rejection of invalid financial inputs."""

    inputs = {
        "S": 100,
        "K": 100,
        "T": 1,
        "r": 0.05,
        "sigma": 0.2,
        "q": 0,
    }

    inputs[parameter] = value

    with pytest.raises(ValueError):
        greeks_options_vectorized(**inputs)


def test_invalid_parameter_inside_array_is_rejected():
    """Verify that one invalid contract invalidates the batch."""

    with pytest.raises(ValueError):

        greeks_options_vectorized(
            S=[100, 100, -1],
            K=100,
            T=1,
            r=0.05,
            sigma=0.2,
        )


def test_incompatible_broadcast_shapes_are_rejected():
    """Verify rejection of incompatible array shapes."""

    with pytest.raises(ValueError):

        greeks_options_vectorized(
            S=[100, 110],
            K=[90, 100, 110],
            T=1,
            r=0.05,
            sigma=0.2,
        )


# ============================================================
# CONSISTENCY WITH EXISTING VECTORIZED PRICING
# ============================================================

def test_prices_match_existing_vectorized_engine():
    """Verify that adding Greeks does not change option prices."""

    inputs = {
        "S": [100, 110, 120],
        "K": [90, 100, 110],
        "T": [1, 0.5, 2],
        "r": 0.05,
        "sigma": [0.2, 0.3, 0.4],
        "q": 0.01,
    }

    calls, puts = price_options_vectorized(**inputs)

    results = greeks_options_vectorized(**inputs)

    np.testing.assert_allclose(
        results["call_price"],
        calls,
        rtol=1e-12,
    )

    np.testing.assert_allclose(
        results["put_price"],
        puts,
        rtol=1e-12,
    )