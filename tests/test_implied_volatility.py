import math

import pytest

from app.pricing.black_scholes import BlackScholes
from app.pricing.implied_volatility import implied_volatility


# TEST 1: Recover known volatility from a call option.
def test_call_iv_recovery():

    engine = BlackScholes(
        S=100,
        K=100,
        T=1.0,
        r=0.05,
        sigma=0.20
    )

    market_price = engine.call_price()

    recovered_iv = implied_volatility(
        market_price=market_price,
        S=100,
        K=100,
        T=1.0,
        r=0.05,
        option_type="call"
    )

    assert recovered_iv == pytest.approx(0.20, abs=1e-6)


# TEST 2: Recover known volatility from a put option.
def test_put_iv_recovery():

    engine = BlackScholes(
        S=100,
        K=110,
        T=0.5,
        r=0.04,
        sigma=0.30
    )

    market_price = engine.put_price()

    recovered_iv = implied_volatility(
        market_price=market_price,
        S=100,
        K=110,
        T=0.5,
        r=0.04,
        option_type="put"
    )

    assert recovered_iv == pytest.approx(0.30, abs=1e-6)


# TEST 3: Verify recovery across multiple volatility levels.
@pytest.mark.parametrize(
    "sigma",
    [0.10, 0.20, 0.30, 0.50, 0.80]
)
def test_multiple_volatility_levels(sigma):

    engine = BlackScholes(
        S=100,
        K=100,
        T=1.0,
        r=0.05,
        sigma=sigma
    )

    market_price = engine.call_price()

    recovered_iv = implied_volatility(
        market_price=market_price,
        S=100,
        K=100,
        T=1.0,
        r=0.05
    )

    assert recovered_iv == pytest.approx(sigma, abs=1e-6)


# TEST 4: Verify dividend yield support.
def test_dividend_yield_iv():

    engine = BlackScholes(
        S=100,
        K=100,
        T=1.0,
        r=0.05,
        sigma=0.25,
        q=0.02
    )

    market_price = engine.call_price()

    recovered_iv = implied_volatility(
        market_price=market_price,
        S=100,
        K=100,
        T=1.0,
        r=0.05,
        option_type="call",
        q=0.02
    )

    assert recovered_iv == pytest.approx(0.25, abs=1e-6)


# TEST 5: Reject market prices above theoretical bounds.
def test_price_above_upper_bound():

    recovered_iv = implied_volatility(
        market_price=150,
        S=100,
        K=100,
        T=1.0,
        r=0.05
    )

    assert math.isnan(recovered_iv)


# TEST 6: Reject market prices below theoretical bounds.
def test_price_below_lower_bound():

    recovered_iv = implied_volatility(
        market_price=0.01,
        S=150,
        K=100,
        T=1.0,
        r=0.05
    )

    assert math.isnan(recovered_iv)


# TEST 7: Reject invalid option types.
def test_invalid_option_type():

    with pytest.raises(ValueError):

        implied_volatility(
            market_price=10,
            S=100,
            K=100,
            T=1.0,
            r=0.05,
            option_type="invalid"
        )


# TEST 8: Reject expired options.
def test_expired_option():

    with pytest.raises(ValueError):

        implied_volatility(
            market_price=10,
            S=100,
            K=100,
            T=0,
            r=0.05
        )


# TEST 9: Reject negative market prices.
def test_negative_market_price():

    with pytest.raises(ValueError):

        implied_volatility(
            market_price=-5,
            S=100,
            K=100,
            T=1.0,
            r=0.05
        )