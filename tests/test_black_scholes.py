import math

import pytest

from app.pricing.black_scholes import BlackScholes


# Test 1: Verify known Black-Scholes pricing results.
def test_known_option_prices():

    engine = BlackScholes(
        S=100,
        K=100,
        T=1,
        r=0.05,
        sigma=0.20
    )

    assert engine.call_price() == pytest.approx(10.4506, abs=1e-4)
    assert engine.put_price() == pytest.approx(5.5735, abs=1e-4)


# Test 2: Verify put-call parity.
def test_put_call_parity():

    S = 100
    K = 105
    T = 0.5
    r = 0.04
    sigma = 0.25
    q = 0.02

    engine = BlackScholes(S, K, T, r, sigma, q)

    # Put-call parity with continuous dividends:
    # C - P = S*exp(-q*T) - K*exp(-r*T)

    left_side = engine.call_price() - engine.put_price()

    right_side = (
        S * math.exp(-q * T)
        - K * math.exp(-r * T)
    )

    assert left_side == pytest.approx(right_side, abs=1e-10)


# Test 3: Verify negative stock prices are rejected.
def test_negative_stock_price():

    with pytest.raises(ValueError):
        BlackScholes(S=-100, K=100, T=1, r=0.05, sigma=0.2)


# Test 4: Verify negative volatility is rejected.
def test_negative_volatility():

    with pytest.raises(ValueError):
        BlackScholes(S=100, K=100, T=1, r=0.05, sigma=-0.2)


# Test 5: Verify expiration payoff.
def test_expired_options():

    engine = BlackScholes(
        S=110,
        K=100,
        T=0,
        r=0.05,
        sigma=0.20
    )

    assert engine.call_price() == 10.0
    assert engine.put_price() == 0.0


# Test 6: Verify zero-volatility pricing.
def test_zero_volatility():

    engine = BlackScholes(
        S=100,
        K=100,
        T=1,
        r=0.05,
        sigma=0
    )

    expected_call = 100 - 100 * math.exp(-0.05)

    assert engine.call_price() == pytest.approx(expected_call)
    assert engine.put_price() == 0.0


# Test 7: Verify delta against a numerical derivative.
def test_call_delta():

    S = 100
    K = 100
    T = 1
    r = 0.05
    sigma = 0.20

    h = 0.01

    price_up = BlackScholes(
        S + h, K, T, r, sigma
    ).call_price()

    price_down = BlackScholes(
        S - h, K, T, r, sigma
    ).call_price()

    numerical_delta = (price_up - price_down) / (2 * h)

    analytical_delta = BlackScholes(
        S, K, T, r, sigma
    ).greeks()["call_delta"]

    assert analytical_delta == pytest.approx(
        numerical_delta,
        abs=1e-4
    )