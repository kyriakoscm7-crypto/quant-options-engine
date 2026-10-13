"""
Automated tests for the Portfolio Risk Analytics Engine.

Tests cover:
- Position input validation.
- Long and short positions.
- Contract multipliers.
- Call and put pricing.
- Position-level Greeks.
- Aggregate portfolio Greeks.
- Expired options.
- Zero-volatility options.
- Undefined Greek handling.
- Numerical consistency.
- Large portfolios.
"""

from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from app.pricing.portfolio import (
    OptionPosition,
    PortfolioAnalytics,
)
from app.pricing.vectorized_black_scholes import (
    greeks_options_vectorized,
)

# ============================================================
# TEST HELPERS
# ============================================================


def make_position(**overrides):
    """Create a valid option position with optional overrides."""

    parameters = {
        "option_type": "call",
        "quantity": 10,
        "S": 100.0,
        "K": 100.0,
        "T": 1.0,
        "r": 0.05,
        "sigma": 0.20,
        "q": 0.0,
        "multiplier": 100,
    }

    parameters.update(overrides)

    return OptionPosition(**parameters)


def make_portfolio(*positions):
    """Create a portfolio from the supplied positions."""

    return PortfolioAnalytics(list(positions))


# ============================================================
# POSITION MODEL TESTS
# ============================================================


def test_valid_call_position():
    """A valid European call position should be accepted."""

    position = make_position()

    assert position.option_type == "call"
    assert position.quantity == 10
    assert position.multiplier == 100


def test_valid_put_position():
    """A valid European put position should be accepted."""

    position = make_position(option_type="put")

    assert position.option_type == "put"


def test_negative_quantity_allowed():
    """Negative quantities represent short option positions."""

    position = make_position(quantity=-5)

    assert position.quantity == -5


def test_custom_contract_multiplier():
    """Contracts can use a multiplier other than 100."""

    position = make_position(multiplier=50)

    assert position.multiplier == 50


def test_default_dividend_yield():
    """The default continuous dividend yield should be zero."""

    position = OptionPosition(
        option_type="call",
        quantity=1,
        S=100,
        K=100,
        T=1,
        r=0.05,
        sigma=0.20,
    )

    assert position.q == 0.0


def test_default_contract_multiplier():
    """The default contract multiplier should be 100."""

    position = make_position()

    assert position.multiplier == 100


def test_position_is_immutable():
    """Frozen dataclasses prevent field reassignment."""

    position = make_position()

    with pytest.raises(FrozenInstanceError):
        position.quantity = 20


@pytest.mark.parametrize(
    "option_type",
    [
        "CALL",
        "PUT",
        "invalid",
        "",
        None,
        123,
    ],
)
def test_invalid_option_type(option_type):
    """Only lowercase 'call' and 'put' are supported."""

    with pytest.raises(ValueError, match="option_type"):
        make_position(option_type=option_type)


@pytest.mark.parametrize(
    "quantity",
    [
        0,
        1.5,
        -2.5,
        "10",
        None,
        True,
        False,
    ],
)
def test_invalid_quantity(quantity):
    """Quantities must be nonzero signed integers."""

    with pytest.raises(ValueError, match="quantity"):
        make_position(quantity=quantity)


@pytest.mark.parametrize(
    "multiplier",
    [
        0,
        -1,
        1.5,
        "100",
        None,
        True,
        False,
    ],
)
def test_invalid_multiplier(multiplier):
    """Multipliers must be positive integers."""

    with pytest.raises(ValueError, match="multiplier"):
        make_position(multiplier=multiplier)


@pytest.mark.parametrize(
    ("parameter", "value"),
    [
        ("S", 0),
        ("S", -100),
        ("K", 0),
        ("K", -100),
        ("T", -1),
        ("sigma", -0.2),
    ],
)
def test_invalid_financial_bounds(parameter, value):
    """Financial parameters must satisfy model constraints."""

    with pytest.raises(ValueError):
        make_position(**{parameter: value})


@pytest.mark.parametrize(
    "parameter",
    ["S", "K", "T", "r", "sigma", "q"],
)
@pytest.mark.parametrize(
    "value",
    [
        np.nan,
        np.inf,
        -np.inf,
        None,
        "invalid",
        True,
        False,
    ],
)
def test_nonfinite_or_invalid_parameters(parameter, value):
    """Reject invalid and non-finite financial inputs."""

    with pytest.raises(ValueError):
        make_position(**{parameter: value})


# ============================================================
# PORTFOLIO INITIALIZATION TESTS
# ============================================================


def test_empty_portfolio_rejected():
    """A portfolio must contain at least one position."""

    with pytest.raises(ValueError, match="at least one"):
        PortfolioAnalytics([])


def test_noniterable_portfolio_rejected():
    """Portfolio input must be iterable."""

    with pytest.raises(ValueError, match="iterable"):
        PortfolioAnalytics(None)


def test_invalid_portfolio_item_rejected():
    """Every portfolio item must be an OptionPosition."""

    with pytest.raises(ValueError, match="OptionPosition"):
        PortfolioAnalytics([make_position(), "invalid"])


def test_different_underlying_prices_rejected():
    """The first version requires one shared underlying price."""

    positions = [
        make_position(S=100),
        make_position(S=110),
    ]

    with pytest.raises(ValueError, match="same underlying"):
        PortfolioAnalytics(positions)


def test_portfolio_accepts_tuple():
    """The constructor accepts iterables such as tuples."""

    portfolio = PortfolioAnalytics(
        (
            make_position(),
            make_position(K=110),
        )
    )

    assert len(portfolio.positions) == 2


# ============================================================
# PORTFOLIO VALUATION TESTS
# ============================================================


def test_single_long_call_value():
    """Long call value equals price times quantity and multiplier."""

    position = make_position(quantity=10)

    result = make_portfolio(position).calculate()

    expected = (
        result["positions"][0]["option_price"]
        * 10
        * 100
    )

    assert result["portfolio_value"] == pytest.approx(expected)


def test_single_short_call_value():
    """Short call positions have negative theoretical value."""

    position = make_position(quantity=-10)

    result = make_portfolio(position).calculate()

    assert result["portfolio_value"] < 0


def test_single_long_put_value():
    """Long put positions have positive theoretical value."""

    position = make_position(
        option_type="put",
        quantity=5,
    )

    result = make_portfolio(position).calculate()

    assert result["portfolio_value"] > 0


def test_single_short_put_value():
    """Short put positions have negative theoretical value."""

    position = make_position(
        option_type="put",
        quantity=-5,
    )

    result = make_portfolio(position).calculate()

    assert result["portfolio_value"] < 0


def test_custom_multiplier_scales_value():
    """Doubling the multiplier doubles position value."""

    standard = make_portfolio(
        make_position(multiplier=100)
    ).calculate()

    doubled = make_portfolio(
        make_position(multiplier=200)
    ).calculate()

    assert doubled["portfolio_value"] == pytest.approx(
        2 * standard["portfolio_value"]
    )


def test_opposite_positions_cancel():
    """Equal long and short positions cancel all defined exposures."""

    positions = [
        make_position(quantity=10),
        make_position(quantity=-10),
    ]

    result = PortfolioAnalytics(positions).calculate()

    for key in (
        "portfolio_value",
        "portfolio_delta",
        "portfolio_gamma",
        "portfolio_vega",
        "portfolio_theta",
        "portfolio_rho",
    ):
        assert result[key] == pytest.approx(0.0, abs=1e-10)


def test_portfolio_value_equals_position_sum():
    """Aggregate value must equal the sum of position values."""

    positions = [
        make_position(quantity=10),
        make_position(
            option_type="put",
            quantity=-5,
            K=95,
        ),
        make_position(
            quantity=20,
            K=110,
            T=0.5,
            sigma=0.25,
        ),
    ]

    result = PortfolioAnalytics(positions).calculate()

    expected = sum(
        position["position_value"]
        for position in result["positions"]
    )

    assert result["portfolio_value"] == pytest.approx(expected)


# ============================================================
# PORTFOLIO GREEKS TESTS
# ============================================================


@pytest.mark.parametrize(
    ("portfolio_key", "position_key"),
    [
        ("portfolio_delta", "delta"),
        ("portfolio_gamma", "gamma"),
        ("portfolio_vega", "vega"),
        ("portfolio_theta", "theta"),
        ("portfolio_rho", "rho"),
    ],
)
def test_portfolio_greek_equals_position_sum(
    portfolio_key,
    position_key,
):
    """Aggregate Greeks equal the sum of position contributions."""

    positions = [
        make_position(quantity=10),
        make_position(
            option_type="put",
            quantity=-5,
            K=95,
        ),
        make_position(
            quantity=20,
            K=110,
            T=0.5,
        ),
    ]

    result = PortfolioAnalytics(positions).calculate()

    expected = sum(
        position[position_key]
        for position in result["positions"]
    )

    assert result[portfolio_key] == pytest.approx(expected)


def test_long_call_has_positive_delta():
    """A standard long call contributes positive delta."""

    result = make_portfolio(
        make_position(option_type="call", quantity=10)
    ).calculate()

    assert result["portfolio_delta"] > 0


def test_long_put_has_negative_delta():
    """A standard long put contributes negative delta."""

    result = make_portfolio(
        make_position(option_type="put", quantity=10)
    ).calculate()

    assert result["portfolio_delta"] < 0


def test_short_call_has_negative_delta():
    """A short call reverses the sign of delta."""

    result = make_portfolio(
        make_position(option_type="call", quantity=-10)
    ).calculate()

    assert result["portfolio_delta"] < 0


def test_short_put_has_positive_delta():
    """A short put reverses the sign of put delta."""

    result = make_portfolio(
        make_position(option_type="put", quantity=-10)
    ).calculate()

    assert result["portfolio_delta"] > 0


def test_long_option_has_positive_gamma():
    """Long standard European options have positive gamma."""

    result = make_portfolio(
        make_position(quantity=10)
    ).calculate()

    assert result["portfolio_gamma"] > 0


def test_short_option_has_negative_gamma():
    """Short standard European options have negative gamma."""

    result = make_portfolio(
        make_position(quantity=-10)
    ).calculate()

    assert result["portfolio_gamma"] < 0


def test_long_option_has_positive_vega():
    """Long standard European options have positive vega."""

    result = make_portfolio(
        make_position(quantity=10)
    ).calculate()

    assert result["portfolio_vega"] > 0


def test_short_option_has_negative_vega():
    """Short standard European options have negative vega."""

    result = make_portfolio(
        make_position(quantity=-10)
    ).calculate()

    assert result["portfolio_vega"] < 0


# ============================================================
# NUMERICAL CONSISTENCY TESTS
# ============================================================


@pytest.mark.parametrize(
    "option_type",
    ["call", "put"],
)
def test_position_matches_vectorized_engine(option_type):
    """Portfolio values and Greeks must match the pricing engine."""

    position = make_position(
        option_type=option_type,
        quantity=7,
        multiplier=50,
        S=100,
        K=105,
        T=0.75,
        r=0.04,
        sigma=0.30,
        q=0.02,
    )

    result = make_portfolio(position).calculate()

    reference = greeks_options_vectorized(
        S=position.S,
        K=position.K,
        T=position.T,
        r=position.r,
        sigma=position.sigma,
        q=position.q,
    )

    exposure = position.quantity * position.multiplier

    expected_price = float(
        reference[f"{option_type}_price"]
    )

    expected_delta = float(
        reference[f"{option_type}_delta"]
    ) * exposure

    expected_theta = float(
        reference[f"{option_type}_theta"]
    ) * exposure

    expected_rho = float(
        reference[f"{option_type}_rho"]
    ) * exposure

    expected_gamma = float(reference["gamma"]) * exposure
    expected_vega = float(reference["vega"]) * exposure

    position_result = result["positions"][0]

    assert position_result["option_price"] == pytest.approx(
        expected_price
    )

    assert position_result["position_value"] == pytest.approx(
        expected_price * exposure
    )

    assert result["portfolio_delta"] == pytest.approx(
        expected_delta
    )

    assert result["portfolio_gamma"] == pytest.approx(
        expected_gamma
    )

    assert result["portfolio_vega"] == pytest.approx(
        expected_vega
    )

    assert result["portfolio_theta"] == pytest.approx(
        expected_theta
    )

    assert result["portfolio_rho"] == pytest.approx(
        expected_rho
    )


# ============================================================
# EXPIRED AND ZERO-VOLATILITY TESTS
# ============================================================


def test_expired_call_uses_intrinsic_value():
    """Expired calls must use intrinsic value."""

    position = make_position(
        option_type="call",
        quantity=3,
        S=110,
        K=100,
        T=0,
    )

    result = make_portfolio(position).calculate()

    assert result["portfolio_value"] == pytest.approx(3000.0)


def test_expired_put_uses_intrinsic_value():
    """Expired puts must use intrinsic value."""

    position = make_position(
        option_type="put",
        quantity=2,
        S=90,
        K=100,
        T=0,
    )

    result = make_portfolio(position).calculate()

    assert result["portfolio_value"] == pytest.approx(2000.0)


def test_expired_option_greeks_undefined():
    """Expired options must return undefined analytical Greeks."""

    result = make_portfolio(
        make_position(T=0)
    ).calculate()

    for key in (
        "portfolio_delta",
        "portfolio_gamma",
        "portfolio_vega",
        "portfolio_theta",
        "portfolio_rho",
    ):
        assert result[key] is None

    for key in ("delta", "gamma", "vega", "theta", "rho"):
        assert result["positions"][0][key] is None


def test_zero_volatility_greeks_undefined():
    """Zero-volatility options have undefined Greeks in this model."""

    result = make_portfolio(
        make_position(sigma=0)
    ).calculate()

    assert result["portfolio_value"] >= 0

    for key in (
        "portfolio_delta",
        "portfolio_gamma",
        "portfolio_vega",
        "portfolio_theta",
        "portfolio_rho",
    ):
        assert result[key] is None


def test_undefined_greek_propagates_to_portfolio():
    """Undefined position Greeks must not be silently treated as zero."""

    positions = [
        make_position(T=1),
        make_position(T=0),
    ]

    result = PortfolioAnalytics(positions).calculate()

    assert result["portfolio_value"] > 0

    for key in (
        "portfolio_delta",
        "portfolio_gamma",
        "portfolio_vega",
        "portfolio_theta",
        "portfolio_rho",
    ):
        assert result[key] is None


# ============================================================
# PORTFOLIO METADATA TESTS
# ============================================================


def test_position_count():
    """Position count must match the number of positions."""

    result = make_portfolio(
        make_position(),
        make_position(K=110),
        make_position(K=120),
    ).calculate()

    assert result["position_count"] == 3


def test_total_contracts():
    """Total contracts count absolute quantities."""

    result = make_portfolio(
        make_position(quantity=10),
        make_position(quantity=-5),
        make_position(quantity=20),
    ).calculate()

    assert result["total_contracts"] == 35


def test_net_contracts():
    """Net contracts preserve the signs of quantities."""

    result = make_portfolio(
        make_position(quantity=10),
        make_position(quantity=-5),
        make_position(quantity=20),
    ).calculate()

    assert result["net_contracts"] == 25


def test_position_order_preserved():
    """The output must preserve the original position order."""

    positions = [
        make_position(K=90),
        make_position(K=100),
        make_position(K=110),
    ]

    result = PortfolioAnalytics(positions).calculate()

    strikes = [
        position["K"]
        for position in result["positions"]
    ]

    assert strikes == [90, 100, 110]


def test_position_indices():
    """Position indices start at zero and follow input order."""

    result = make_portfolio(
        make_position(),
        make_position(K=110),
        make_position(K=120),
    ).calculate()

    indices = [
        position["position_index"]
        for position in result["positions"]
    ]

    assert indices == [0, 1, 2]


def test_large_portfolio():
    """The engine should process a large portfolio successfully."""

    positions = [
        make_position(
            K=80 + (index % 41),
            T=0.25 + (index % 10) * 0.1,
            sigma=0.15 + (index % 10) * 0.01,
            quantity=1 if index % 2 == 0 else -1,
        )
        for index in range(10_000)
    ]

    result = PortfolioAnalytics(positions).calculate()

    assert result["position_count"] == 10_000
    assert result["total_contracts"] == 10_000
    assert len(result["positions"]) == 10_000

    assert np.isfinite(result["portfolio_value"])
    assert np.isfinite(result["portfolio_delta"])
    assert np.isfinite(result["portfolio_gamma"])
    assert np.isfinite(result["portfolio_vega"])
    assert np.isfinite(result["portfolio_theta"])
    assert np.isfinite(result["portfolio_rho"])
