"""
Automated tests for the Portfolio Scenario Analysis Engine.

Tests cover:
- MarketScenario input validation.
- PortfolioScenarioAnalysis initialization.
- Full Black-Scholes scenario repricing.
- Underlying price shocks.
- Absolute volatility shocks.
- Calendar-day time advancement.
- Expired options and zero volatility.
- Long and short positions.
- Contract multipliers.
- Portfolio-level and position-level P&L.
- Scenario percentage changes.
- Vectorized scenario matrices.
- Preservation of original portfolio positions.
"""

import math
from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from app.pricing.portfolio import OptionPosition, PortfolioAnalytics
from app.pricing.scenario_analysis import (
    MarketScenario,
    PortfolioScenarioAnalysis,
)
from app.pricing.vectorized_black_scholes import price_options_vectorized

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
    """Create a portfolio, defaulting to one long call."""

    if not positions:
        positions = (make_position(),)

    return PortfolioAnalytics(positions)


def make_analysis(
    positions=None,
    scenarios=None,
):
    """Build a scenario analysis using valid default inputs."""

    if positions is None:
        positions = [make_position()]

    if scenarios is None:
        scenarios = [MarketScenario(name="Base Case")]

    return PortfolioScenarioAnalysis(
        portfolio=PortfolioAnalytics(positions),
        scenarios=scenarios,
    )


def get_single_scenario(
    positions=None,
    scenario=None,
):
    """Return the first scenario result from an analysis."""

    if scenario is None:
        scenario = MarketScenario(name="Test Scenario")

    result = make_analysis(
        positions=positions,
        scenarios=[scenario],
    ).calculate()

    return result, result["scenarios"][0]


def independently_price_position(
    position,
    price_change_pct=0.0,
    volatility_change=0.0,
    days_forward=0.0,
):
    """
    Independently reprice a position using the vectorized engine.

    This helper does not call PortfolioScenarioAnalysis.
    """

    scenario_S = (
        position.S * (1.0 + price_change_pct / 100.0)
    )

    scenario_sigma = position.sigma + volatility_change

    scenario_T = max(
        position.T - days_forward / 365.0,
        0.0,
    )

    calls, puts = price_options_vectorized(
        S=scenario_S,
        K=position.K,
        T=scenario_T,
        r=position.r,
        sigma=scenario_sigma,
        q=position.q,
    )

    option_price = (
        calls if position.option_type == "call" else puts
    )

    return float(
        np.asarray(option_price)
    ) * position.quantity * position.multiplier


# ============================================================
# MARKET SCENARIO MODEL TESTS
# ============================================================


def test_default_scenario_values():
    scenario = MarketScenario(name="Base Case")

    assert scenario.name == "Base Case"
    assert scenario.price_change_pct == 0.0
    assert scenario.volatility_change == 0.0
    assert scenario.days_forward == 0.0


def test_valid_negative_price_shock():
    scenario = MarketScenario(
        name="Decline",
        price_change_pct=-5.0,
    )

    assert scenario.price_change_pct == -5.0


def test_valid_positive_price_shock():
    scenario = MarketScenario(
        name="Rally",
        price_change_pct=10.0,
    )

    assert scenario.price_change_pct == 10.0


def test_valid_negative_volatility_shock():
    scenario = MarketScenario(
        name="Volatility Decline",
        volatility_change=-0.05,
    )

    assert scenario.volatility_change == -0.05


def test_valid_time_advancement():
    scenario = MarketScenario(
        name="Seven Days",
        days_forward=7,
    )

    assert scenario.days_forward == 7


def test_scenario_is_immutable():
    scenario = MarketScenario(name="Base Case")

    with pytest.raises(FrozenInstanceError):
        scenario.name = "Modified"


@pytest.mark.parametrize(
    "invalid_name",
    [
        "",
        "   ",
        None,
        123,
        True,
        [],
    ],
)
def test_invalid_scenario_name(invalid_name):
    with pytest.raises(ValueError):
        MarketScenario(name=invalid_name)


@pytest.mark.parametrize(
    "parameter",
    [
        "price_change_pct",
        "volatility_change",
        "days_forward",
    ],
)
@pytest.mark.parametrize(
    "invalid_value",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
        None,
        "invalid",
        True,
        False,
    ],
)
def test_invalid_numeric_scenario_parameters(
    parameter,
    invalid_value,
):
    parameters = {"name": "Invalid Scenario"}
    parameters[parameter] = invalid_value

    with pytest.raises(ValueError):
        MarketScenario(**parameters)


@pytest.mark.parametrize(
    "price_change_pct",
    [
        -100.0,
        -101.0,
        -200.0,
    ],
)
def test_invalid_price_shock(price_change_pct):
    with pytest.raises(ValueError):
        MarketScenario(
            name="Invalid Price Shock",
            price_change_pct=price_change_pct,
        )


@pytest.mark.parametrize(
    "days_forward",
    [
        -1,
        -0.5,
        -365,
    ],
)
def test_negative_days_forward(days_forward):
    with pytest.raises(ValueError):
        MarketScenario(
            name="Invalid Time",
            days_forward=days_forward,
        )


def test_price_shock_just_above_negative_100_allowed():
    scenario = MarketScenario(
        name="Near Total Decline",
        price_change_pct=-99.9,
    )

    assert scenario.price_change_pct == -99.9


def test_large_positive_price_shock_allowed():
    scenario = MarketScenario(
        name="Large Rally",
        price_change_pct=200.0,
    )

    assert scenario.price_change_pct == 200.0


# ============================================================
# ANALYSIS INITIALIZATION TESTS
# ============================================================


def test_invalid_portfolio_object():
    with pytest.raises(ValueError):
        PortfolioScenarioAnalysis(
            portfolio=[],
            scenarios=[MarketScenario(name="Base")],
        )


def test_empty_scenarios_rejected():
    with pytest.raises(ValueError):
        PortfolioScenarioAnalysis(
            portfolio=make_portfolio(),
            scenarios=[],
        )


def test_noniterable_scenarios_rejected():
    with pytest.raises(ValueError):
        PortfolioScenarioAnalysis(
            portfolio=make_portfolio(),
            scenarios=123,
        )


def test_invalid_scenario_item_rejected():
    with pytest.raises(ValueError):
        PortfolioScenarioAnalysis(
            portfolio=make_portfolio(),
            scenarios=["not a scenario"],
        )


def test_duplicate_scenario_names_rejected():
    with pytest.raises(ValueError):
        PortfolioScenarioAnalysis(
            portfolio=make_portfolio(),
            scenarios=[
                MarketScenario(name="Duplicate"),
                MarketScenario(name="Duplicate"),
            ],
        )


def test_scenario_tuple_accepted():
    analysis = PortfolioScenarioAnalysis(
        portfolio=make_portfolio(),
        scenarios=(
            MarketScenario(name="First"),
            MarketScenario(name="Second"),
        ),
    )

    assert len(analysis.scenarios) == 2


def test_scenario_generator_accepted():
    scenarios = (
        MarketScenario(name=f"Scenario {index}")
        for index in range(3)
    )

    analysis = PortfolioScenarioAnalysis(
        portfolio=make_portfolio(),
        scenarios=scenarios,
    )

    assert len(analysis.scenarios) == 3


def test_original_portfolio_reference_preserved():
    portfolio = make_portfolio()

    analysis = PortfolioScenarioAnalysis(
        portfolio=portfolio,
        scenarios=[MarketScenario(name="Base")],
    )

    assert analysis.portfolio is portfolio


# ============================================================
# BASELINE VALUATION TESTS
# ============================================================


def test_original_value_matches_portfolio_engine():
    positions = [
        make_position(),
        make_position(
            option_type="put",
            quantity=-5,
            K=95.0,
        ),
        make_position(
            quantity=20,
            K=110.0,
            T=0.5,
            sigma=0.25,
        ),
    ]

    portfolio = PortfolioAnalytics(positions)

    analysis = PortfolioScenarioAnalysis(
        portfolio=portfolio,
        scenarios=[MarketScenario(name="Base")],
    )

    result = analysis.calculate()

    expected = portfolio.calculate()["portfolio_value"]

    assert result["original_portfolio_value"] == pytest.approx(
        expected,
        abs=1e-8,
    )


def test_known_portfolio_original_value():
    positions = [
        make_position(),
        make_position(
            option_type="put",
            quantity=-5,
            K=95.0,
        ),
        make_position(
            quantity=20,
            K=110.0,
            T=0.5,
            sigma=0.25,
        ),
    ]

    result = make_analysis(
        positions=positions,
    ).calculate()

    assert result["original_portfolio_value"] == pytest.approx(
        17045.518221382,
        abs=1e-6,
    )


def test_no_change_scenario_has_zero_pnl():
    result, scenario = get_single_scenario()

    assert scenario["scenario_portfolio_value"] == pytest.approx(
        result["original_portfolio_value"],
        abs=1e-10,
    )

    assert scenario["scenario_pnl"] == pytest.approx(
        0.0,
        abs=1e-10,
    )


def test_no_change_position_pnl_is_zero():
    _, scenario = get_single_scenario(
        positions=[
            make_position(),
            make_position(
                option_type="put",
                quantity=-5,
            ),
        ],
    )

    for position in scenario["positions"]:
        assert position["position_pnl"] == pytest.approx(
            0.0,
            abs=1e-10,
        )


# ============================================================
# UNDERLYING PRICE SHOCK TESTS
# ============================================================


@pytest.mark.parametrize(
    "price_change_pct",
    [
        -20.0,
        -10.0,
        -5.0,
        -1.0,
        0.0,
        1.0,
        5.0,
        10.0,
        20.0,
    ],
)
def test_call_price_shocks_match_independent_pricing(
    price_change_pct,
):
    position = make_position()

    _, scenario = get_single_scenario(
        positions=[position],
        scenario=MarketScenario(
            name="Price Shock",
            price_change_pct=price_change_pct,
        ),
    )

    expected = independently_price_position(
        position,
        price_change_pct=price_change_pct,
    )

    assert scenario["scenario_portfolio_value"] == pytest.approx(
        expected,
        abs=1e-8,
    )


@pytest.mark.parametrize(
    "price_change_pct",
    [
        -20.0,
        -5.0,
        0.0,
        5.0,
        20.0,
    ],
)
def test_put_price_shocks_match_independent_pricing(
    price_change_pct,
):
    position = make_position(option_type="put")

    _, scenario = get_single_scenario(
        positions=[position],
        scenario=MarketScenario(
            name="Put Price Shock",
            price_change_pct=price_change_pct,
        ),
    )

    expected = independently_price_position(
        position,
        price_change_pct=price_change_pct,
    )

    assert scenario["scenario_portfolio_value"] == pytest.approx(
        expected,
        abs=1e-8,
    )


def test_long_call_gains_from_price_increase():
    _, scenario = get_single_scenario(
        scenario=MarketScenario(
            name="Rally",
            price_change_pct=5.0,
        ),
    )

    assert scenario["scenario_pnl"] > 0


def test_long_call_loses_from_price_decrease():
    _, scenario = get_single_scenario(
        scenario=MarketScenario(
            name="Decline",
            price_change_pct=-5.0,
        ),
    )

    assert scenario["scenario_pnl"] < 0


def test_long_put_gains_from_price_decrease():
    _, scenario = get_single_scenario(
        positions=[make_position(option_type="put")],
        scenario=MarketScenario(
            name="Decline",
            price_change_pct=-5.0,
        ),
    )

    assert scenario["scenario_pnl"] > 0


def test_long_put_loses_from_price_increase():
    _, scenario = get_single_scenario(
        positions=[make_position(option_type="put")],
        scenario=MarketScenario(
            name="Rally",
            price_change_pct=5.0,
        ),
    )

    assert scenario["scenario_pnl"] < 0


# ============================================================
# VOLATILITY SHOCK TESTS
# ============================================================


@pytest.mark.parametrize(
    "volatility_change",
    [
        -0.10,
        -0.05,
        0.0,
        0.05,
        0.10,
    ],
)
def test_volatility_shock_matches_independent_pricing(
    volatility_change,
):
    position = make_position()

    _, scenario = get_single_scenario(
        positions=[position],
        scenario=MarketScenario(
            name="Volatility Shock",
            volatility_change=volatility_change,
        ),
    )

    expected = independently_price_position(
        position,
        volatility_change=volatility_change,
    )

    assert scenario["scenario_portfolio_value"] == pytest.approx(
        expected,
        abs=1e-8,
    )


def test_positive_volatility_shock_increases_long_call_value():
    _, scenario = get_single_scenario(
        scenario=MarketScenario(
            name="Higher Volatility",
            volatility_change=0.05,
        ),
    )

    assert scenario["scenario_pnl"] > 0


def test_negative_volatility_shock_decreases_long_call_value():
    _, scenario = get_single_scenario(
        scenario=MarketScenario(
            name="Lower Volatility",
            volatility_change=-0.05,
        ),
    )

    assert scenario["scenario_pnl"] < 0


def test_zero_scenario_volatility_allowed():
    position = make_position(sigma=0.20)

    _, scenario = get_single_scenario(
        positions=[position],
        scenario=MarketScenario(
            name="Zero Volatility",
            volatility_change=-0.20,
        ),
    )

    expected = independently_price_position(
        position,
        volatility_change=-0.20,
    )

    assert scenario["scenario_portfolio_value"] == pytest.approx(
        expected,
        abs=1e-8,
    )


def test_negative_scenario_volatility_rejected():
    analysis = make_analysis(
        scenarios=[
            MarketScenario(
                name="Invalid Volatility",
                volatility_change=-0.30,
            ),
        ],
    )

    with pytest.raises(ValueError):
        analysis.calculate()


def test_negative_volatility_for_one_position_rejected():
    positions = [
        make_position(sigma=0.10),
        make_position(sigma=0.30, K=110.0),
    ]

    analysis = make_analysis(
        positions=positions,
        scenarios=[
            MarketScenario(
                name="Invalid For First Position",
                volatility_change=-0.15,
            ),
        ],
    )

    with pytest.raises(ValueError):
        analysis.calculate()


# ============================================================
# TIME ADVANCEMENT TESTS
# ============================================================


@pytest.mark.parametrize(
    "days_forward",
    [
        0.0,
        1.0,
        7.0,
        30.0,
        90.0,
        365.0,
    ],
)
def test_time_advancement_matches_independent_pricing(
    days_forward,
):
    position = make_position()

    _, scenario = get_single_scenario(
        positions=[position],
        scenario=MarketScenario(
            name="Time Advancement",
            days_forward=days_forward,
        ),
    )

    expected = independently_price_position(
        position,
        days_forward=days_forward,
    )

    assert scenario["scenario_portfolio_value"] == pytest.approx(
        expected,
        abs=1e-8,
    )


def test_long_atm_call_loses_value_as_time_passes():
    _, scenario = get_single_scenario(
        scenario=MarketScenario(
            name="Time Decay",
            days_forward=7.0,
        ),
    )

    assert scenario["scenario_pnl"] < 0


def test_option_expiring_during_scenario():
    position = make_position(
        S=110.0,
        K=100.0,
        T=5.0 / 365.0,
    )

    _, scenario = get_single_scenario(
        positions=[position],
        scenario=MarketScenario(
            name="Expiration",
            days_forward=10.0,
        ),
    )

    assert scenario["positions"][0][
        "scenario_option_price"
    ] == pytest.approx(10.0)


def test_expired_out_of_money_call_has_zero_value():
    position = make_position(
        S=90.0,
        K=100.0,
        T=0.0,
    )

    _, scenario = get_single_scenario(
        positions=[position],
    )

    assert scenario["scenario_portfolio_value"] == pytest.approx(
        0.0,
    )


def test_expired_in_money_put_uses_intrinsic_value():
    position = make_position(
        option_type="put",
        S=90.0,
        K=100.0,
        T=0.0,
        quantity=3,
    )

    _, scenario = get_single_scenario(
        positions=[position],
    )

    assert scenario["scenario_portfolio_value"] == pytest.approx(
        3000.0,
    )


def test_days_forward_beyond_expiration():
    position = make_position(
        S=110.0,
        K=100.0,
        T=0.1,
    )

    _, scenario = get_single_scenario(
        positions=[position],
        scenario=MarketScenario(
            name="Far Beyond Expiration",
            days_forward=1000.0,
        ),
    )

    assert scenario["positions"][0][
        "scenario_option_price"
    ] == pytest.approx(10.0)


# ============================================================
# LONG, SHORT, AND MULTIPLIER TESTS
# ============================================================


def test_short_call_pnl_opposite_of_long_call():
    shock = MarketScenario(
        name="Price Rally",
        price_change_pct=5.0,
    )

    _, long_result = get_single_scenario(
        positions=[make_position(quantity=10)],
        scenario=shock,
    )

    _, short_result = get_single_scenario(
        positions=[make_position(quantity=-10)],
        scenario=shock,
    )

    assert short_result["scenario_pnl"] == pytest.approx(
        -long_result["scenario_pnl"],
    )


def test_short_put_pnl_opposite_of_long_put():
    shock = MarketScenario(
        name="Price Decline",
        price_change_pct=-5.0,
    )

    _, long_result = get_single_scenario(
        positions=[
            make_position(
                option_type="put",
                quantity=10,
            ),
        ],
        scenario=shock,
    )

    _, short_result = get_single_scenario(
        positions=[
            make_position(
                option_type="put",
                quantity=-10,
            ),
        ],
        scenario=shock,
    )

    assert short_result["scenario_pnl"] == pytest.approx(
        -long_result["scenario_pnl"],
    )


def test_custom_multiplier_scales_scenario_pnl():
    shock = MarketScenario(
        name="Price Rally",
        price_change_pct=5.0,
    )

    _, standard = get_single_scenario(
        positions=[make_position(multiplier=100)],
        scenario=shock,
    )

    _, custom = get_single_scenario(
        positions=[make_position(multiplier=200)],
        scenario=shock,
    )

    assert custom["scenario_pnl"] == pytest.approx(
        2.0 * standard["scenario_pnl"],
    )


def test_opposite_positions_cancel_scenario_pnl():
    positions = [
        make_position(quantity=10),
        make_position(quantity=-10),
    ]

    _, scenario = get_single_scenario(
        positions=positions,
        scenario=MarketScenario(
            name="Price Shock",
            price_change_pct=10.0,
        ),
    )

    assert scenario["scenario_pnl"] == pytest.approx(
        0.0,
        abs=1e-10,
    )


def test_opposite_positions_have_zero_portfolio_value():
    positions = [
        make_position(quantity=10),
        make_position(quantity=-10),
    ]

    result, scenario = get_single_scenario(
        positions=positions,
        scenario=MarketScenario(
            name="Price Shock",
            price_change_pct=10.0,
        ),
    )

    assert result["original_portfolio_value"] == pytest.approx(
        0.0,
        abs=1e-10,
    )

    assert scenario["scenario_portfolio_value"] == pytest.approx(
        0.0,
        abs=1e-10,
    )


# ============================================================
# P&L AGGREGATION TESTS
# ============================================================


def test_scenario_pnl_equals_value_difference():
    result, scenario = get_single_scenario(
        scenario=MarketScenario(
            name="Combined Shock",
            price_change_pct=-5.0,
            volatility_change=0.05,
            days_forward=7.0,
        ),
    )

    expected = (
        scenario["scenario_portfolio_value"]
        - result["original_portfolio_value"]
    )

    assert scenario["scenario_pnl"] == pytest.approx(
        expected,
        abs=1e-8,
    )


def test_scenario_pnl_equals_sum_of_position_pnl():
    positions = [
        make_position(),
        make_position(
            option_type="put",
            quantity=-5,
            K=95.0,
        ),
        make_position(
            K=110.0,
            T=0.5,
            sigma=0.25,
            quantity=20,
        ),
    ]

    _, scenario = get_single_scenario(
        positions=positions,
        scenario=MarketScenario(
            name="Combined Shock",
            price_change_pct=-5.0,
            volatility_change=0.05,
            days_forward=7.0,
        ),
    )

    expected = sum(
        position["position_pnl"]
        for position in scenario["positions"]
    )

    assert scenario["scenario_pnl"] == pytest.approx(
        expected,
        abs=1e-8,
    )


def test_scenario_value_equals_sum_of_position_values():
    positions = [
        make_position(),
        make_position(
            option_type="put",
            quantity=-5,
        ),
    ]

    _, scenario = get_single_scenario(
        positions=positions,
        scenario=MarketScenario(
            name="Price Shock",
            price_change_pct=5.0,
        ),
    )

    expected = sum(
        position["scenario_position_value"]
        for position in scenario["positions"]
    )

    assert scenario["scenario_portfolio_value"] == pytest.approx(
        expected,
        abs=1e-8,
    )


def test_position_pnl_equals_position_value_difference():
    _, scenario = get_single_scenario(
        scenario=MarketScenario(
            name="Price Shock",
            price_change_pct=5.0,
        ),
    )

    for position in scenario["positions"]:
        expected = (
            position["scenario_position_value"]
            - position["original_position_value"]
        )

        assert position["position_pnl"] == pytest.approx(
            expected,
            abs=1e-8,
        )


# ============================================================
# SCENARIO PERCENTAGE TESTS
# ============================================================


def test_scenario_return_percentage():
    result, scenario = get_single_scenario(
        scenario=MarketScenario(
            name="Rally",
            price_change_pct=5.0,
        ),
    )

    expected = (
        scenario["scenario_pnl"]
        / abs(result["original_portfolio_value"])
        * 100.0
    )

    assert scenario["scenario_return_pct"] == pytest.approx(
        expected,
    )


def test_negative_original_value_return_percentage():
    result, scenario = get_single_scenario(
        positions=[make_position(quantity=-10)],
        scenario=MarketScenario(
            name="Rally",
            price_change_pct=5.0,
        ),
    )

    assert result["original_portfolio_value"] < 0

    expected = (
        scenario["scenario_pnl"]
        / abs(result["original_portfolio_value"])
        * 100.0
    )

    assert scenario["scenario_return_pct"] == pytest.approx(
        expected,
    )


def test_zero_original_value_has_undefined_return():
    positions = [
        make_position(quantity=10),
        make_position(quantity=-10),
    ]

    _, scenario = get_single_scenario(
        positions=positions,
        scenario=MarketScenario(
            name="Price Shock",
            price_change_pct=5.0,
        ),
    )

    assert scenario["scenario_return_pct"] is None


# ============================================================
# OUTPUT STRUCTURE TESTS
# ============================================================


def test_scenario_count():
    result = make_analysis(
        scenarios=[
            MarketScenario(name="First"),
            MarketScenario(name="Second"),
            MarketScenario(name="Third"),
        ],
    ).calculate()

    assert result["scenario_count"] == 3


def test_position_count():
    result = make_analysis(
        positions=[
            make_position(),
            make_position(option_type="put"),
            make_position(K=110.0),
        ],
    ).calculate()

    assert result["position_count"] == 3


def test_scenario_order_preserved():
    names = [
        "Crash",
        "Decline",
        "Base",
        "Rally",
    ]

    result = make_analysis(
        scenarios=[
            MarketScenario(name=name)
            for name in names
        ],
    ).calculate()

    assert [
        scenario["name"]
        for scenario in result["scenarios"]
    ] == names


def test_position_order_preserved():
    positions = [
        make_position(K=90.0),
        make_position(K=100.0),
        make_position(K=110.0),
    ]

    _, scenario = get_single_scenario(
        positions=positions,
    )

    assert [
        position["position_index"]
        for position in scenario["positions"]
    ] == [0, 1, 2]


def test_scenario_metadata_preserved():
    market_scenario = MarketScenario(
        name="Combined Shock",
        price_change_pct=-5.0,
        volatility_change=0.05,
        days_forward=7.0,
    )

    _, scenario = get_single_scenario(
        scenario=market_scenario,
    )

    assert scenario["name"] == "Combined Shock"
    assert scenario["price_change_pct"] == -5.0
    assert scenario["volatility_change"] == 0.05
    assert scenario["days_forward"] == 7.0


def test_position_metadata_preserved():
    position = make_position(
        option_type="put",
        quantity=-7,
        multiplier=50,
    )

    _, scenario = get_single_scenario(
        positions=[position],
    )

    position_result = scenario["positions"][0]

    assert position_result["option_type"] == "put"
    assert position_result["quantity"] == -7
    assert position_result["multiplier"] == 50


# ============================================================
# ORIGINAL POSITION IMMUTABILITY TESTS
# ============================================================


def test_scenario_analysis_does_not_modify_positions():
    positions = [
        make_position(),
        make_position(
            option_type="put",
            K=95.0,
            sigma=0.30,
        ),
    ]

    original_positions = tuple(positions)

    analysis = make_analysis(
        positions=positions,
        scenarios=[
            MarketScenario(
                name="Combined Shock",
                price_change_pct=-10.0,
                volatility_change=0.05,
                days_forward=30.0,
            ),
        ],
    )

    analysis.calculate()

    assert tuple(analysis.portfolio.positions) == original_positions


def test_repeated_calculation_is_consistent():
    analysis = make_analysis(
        scenarios=[
            MarketScenario(
                name="Rally",
                price_change_pct=5.0,
            ),
        ],
    )

    first = analysis.calculate()
    second = analysis.calculate()

    assert first == second


# ============================================================
# MULTIPLE SCENARIO TESTS
# ============================================================


def test_multiple_scenarios_have_distinct_values():
    result = make_analysis(
        scenarios=[
            MarketScenario(
                name="Decline",
                price_change_pct=-5.0,
            ),
            MarketScenario(
                name="Base",
            ),
            MarketScenario(
                name="Rally",
                price_change_pct=5.0,
            ),
        ],
    ).calculate()

    values = [
        scenario["scenario_portfolio_value"]
        for scenario in result["scenarios"]
    ]

    assert values[0] < values[1] < values[2]


def test_combined_shock_matches_independent_pricing():
    positions = [
        make_position(),
        make_position(
            option_type="put",
            quantity=-5,
            K=95.0,
        ),
        make_position(
            K=110.0,
            sigma=0.25,
            T=0.5,
            quantity=20,
        ),
    ]

    scenario = MarketScenario(
        name="Combined Shock",
        price_change_pct=-5.0,
        volatility_change=0.05,
        days_forward=7.0,
    )

    _, result = get_single_scenario(
        positions=positions,
        scenario=scenario,
    )

    expected = sum(
        independently_price_position(
            position,
            price_change_pct=scenario.price_change_pct,
            volatility_change=scenario.volatility_change,
            days_forward=scenario.days_forward,
        )
        for position in positions
    )

    assert result["scenario_portfolio_value"] == pytest.approx(
        expected,
        abs=1e-8,
    )


# ============================================================
# LARGE VECTORIZED SCENARIO MATRIX TEST
# ============================================================


def test_large_scenario_matrix():
    """
    Test 100 positions across 50 scenarios.

    This produces 5,000 scenario-position combinations.
    """

    positions = [
        make_position(
            option_type=(
                "call" if index % 2 == 0 else "put"
            ),
            quantity=(
                10 if index % 3 != 0 else -5
            ),
            K=80.0 + (index % 41),
            T=0.1 + (index % 20) / 20.0,
            sigma=0.15 + (index % 10) / 100.0,
        )
        for index in range(100)
    ]

    scenarios = [
        MarketScenario(
            name=f"Scenario {index}",
            price_change_pct=-10.0 + index * 0.4,
            volatility_change=-0.05 + index * 0.002,
            days_forward=index,
        )
        for index in range(50)
    ]

    result = make_analysis(
        positions=positions,
        scenarios=scenarios,
    ).calculate()

    assert result["position_count"] == 100
    assert result["scenario_count"] == 50
    assert len(result["scenarios"]) == 50

    for scenario in result["scenarios"]:
        assert len(scenario["positions"]) == 100

        assert math.isfinite(
            scenario["scenario_portfolio_value"]
        )

        assert math.isfinite(
            scenario["scenario_pnl"]
        )


# ============================================================
# FINANCIAL CONSISTENCY TESTS
# ============================================================


def test_price_shock_direction_for_long_call():
    scenarios = [
        MarketScenario(
            name="Decline",
            price_change_pct=-10.0,
        ),
        MarketScenario(
            name="Base",
        ),
        MarketScenario(
            name="Rally",
            price_change_pct=10.0,
        ),
    ]

    result = make_analysis(
        scenarios=scenarios,
    ).calculate()

    pnls = [
        scenario["scenario_pnl"]
        for scenario in result["scenarios"]
    ]

    assert pnls[0] < 0
    assert pnls[1] == pytest.approx(0.0)
    assert pnls[2] > 0


def test_volatility_shock_direction_for_long_call():
    scenarios = [
        MarketScenario(
            name="Lower Volatility",
            volatility_change=-0.05,
        ),
        MarketScenario(
            name="Base",
        ),
        MarketScenario(
            name="Higher Volatility",
            volatility_change=0.05,
        ),
    ]

    result = make_analysis(
        scenarios=scenarios,
    ).calculate()

    pnls = [
        scenario["scenario_pnl"]
        for scenario in result["scenarios"]
    ]

    assert pnls[0] < 0
    assert pnls[1] == pytest.approx(0.0)
    assert pnls[2] > 0


def test_scenario_pnl_sign_for_short_call():
    _, scenario = get_single_scenario(
        positions=[make_position(quantity=-10)],
        scenario=MarketScenario(
            name="Rally",
            price_change_pct=5.0,
        ),
    )

    assert scenario["scenario_pnl"] < 0