"""
Automated tests for the Portfolio Risk Analytics REST API.

Endpoints tested:
    POST /api/v1/portfolio/value
    POST /api/v1/portfolio/greeks
    POST /api/v1/portfolio/scenarios

Test coverage includes:
    - Successful portfolio valuation.
    - Aggregate portfolio Greeks.
    - Portfolio scenario analysis.
    - Long and short option positions.
    - Position-level calculations.
    - Invalid request validation.
    - Expired options.
    - Zero volatility.
    - Scenario price, volatility, and time shocks.
    - Financial consistency between API endpoints.
    - Maximum request-size validation.
"""

import json
import math

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.pricing.portfolio import OptionPosition, PortfolioAnalytics
from app.pricing.scenario_analysis import (
    MarketScenario,
    PortfolioScenarioAnalysis,
)

# ============================================================
# FASTAPI TEST CLIENT
# ============================================================

# TestClient sends requests directly to the FastAPI application.
#
# This means:
# - No running Uvicorn server is required.
# - No network requests are made.
# - Tests execute locally and quickly.
# - HTTP status codes and JSON responses can be verified.
client = TestClient(app)


# ============================================================
# API ENDPOINT CONSTANTS
# ============================================================

VALUE_ENDPOINT = "/api/v1/portfolio/value"

GREEKS_ENDPOINT = "/api/v1/portfolio/greeks"

SCENARIOS_ENDPOINT = "/api/v1/portfolio/scenarios"


# ============================================================
# TEST HELPERS
# ============================================================

def make_position(**overrides):
    """
    Create a valid API position dictionary.

    Any field can be overridden for a specific test.
    """

    position = {
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

    position.update(overrides)

    return position


def make_portfolio_request(positions=None):
    """
    Build a valid portfolio API request.
    """

    if positions is None:
        positions = [make_position()]

    return {
        "positions": positions,
    }


def make_scenario(**overrides):
    """
    Create a valid market scenario dictionary.
    """

    scenario = {
        "name": "Base Case",
        "price_change_pct": 0.0,
        "volatility_change": 0.0,
        "days_forward": 0.0,
    }

    scenario.update(overrides)

    return scenario


def make_scenario_request(
    positions=None,
    scenarios=None,
):
    """
    Build a valid portfolio scenario API request.
    """

    if positions is None:
        positions = [make_position()]

    if scenarios is None:
        scenarios = [make_scenario()]

    return {
        "positions": positions,
        "scenarios": scenarios,
    }


def make_domain_portfolio(position_dicts):
    """
    Convert API dictionaries into OptionPosition objects.

    This allows us to independently compare API responses
    against the underlying PortfolioAnalytics engine.
    """

    positions = [
        OptionPosition(**position)
        for position in position_dicts
    ]

    return PortfolioAnalytics(positions)


def assert_http_422(endpoint, payload):
    """
    Verify that an invalid request produces HTTP 422.

    HTTP 422 indicates that the submitted request
    failed input validation.
    """

    # Serialize the payload ourselves so non-finite values such as
    # NaN, Infinity, and -Infinity can reach the API validation layer.
    #
    # HTTPX's json= argument rejects these values before sending
    # the request, which would test HTTPX rather than our API.
    #
    # This deliberately sends nonstandard JSON tokens to verify
    # that the API rejects invalid numerical inputs.
    body = json.dumps(payload, allow_nan=True)

    response = client.post(
        endpoint,
        content=body,
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422, response.text


# ============================================================
# SECTION 1: PORTFOLIO VALUATION ENDPOINT
# ============================================================

def test_portfolio_value_success():
    """
    Verify successful valuation of a single call position.
    """

    response = client.post(
        VALUE_ENDPOINT,
        json=make_portfolio_request(),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["position_count"] == 1
    assert data["total_contracts"] == 10
    assert data["net_contracts"] == 10

    assert data["portfolio_value"] > 0

    assert len(data["positions"]) == 1


def test_portfolio_value_matches_domain_engine():
    """
    Compare the API valuation with PortfolioAnalytics.
    """

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

    response = client.post(
        VALUE_ENDPOINT,
        json=make_portfolio_request(positions),
    )

    assert response.status_code == 200

    expected = make_domain_portfolio(
        positions
    ).calculate()

    actual = response.json()

    assert actual["portfolio_value"] == pytest.approx(
        expected["portfolio_value"],
    )

    assert actual["position_count"] == 3


def test_known_portfolio_value():
    """
    Verify the known three-position portfolio example.
    """

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

    response = client.post(
        VALUE_ENDPOINT,
        json=make_portfolio_request(positions),
    )

    assert response.status_code == 200

    assert response.json()["portfolio_value"] == pytest.approx(
        17045.518221382,
        abs=1e-6,
    )


def test_portfolio_value_position_breakdown():
    """
    Verify that each position contains its theoretical value.
    """

    response = client.post(
        VALUE_ENDPOINT,
        json=make_portfolio_request(),
    )

    assert response.status_code == 200

    position = response.json()["positions"][0]

    assert position["position_index"] == 0
    assert position["option_type"] == "call"
    assert position["quantity"] == 10
    assert position["multiplier"] == 100

    assert position["option_price"] > 0
    assert position["position_value"] > 0


def test_portfolio_value_excludes_greeks():
    """
    The valuation endpoint should not expose aggregate Greeks.

    Those values belong to the dedicated Greeks endpoint.
    """

    response = client.post(
        VALUE_ENDPOINT,
        json=make_portfolio_request(),
    )

    assert response.status_code == 200

    data = response.json()

    assert "portfolio_delta" not in data
    assert "portfolio_gamma" not in data
    assert "portfolio_vega" not in data
    assert "portfolio_theta" not in data
    assert "portfolio_rho" not in data


def test_portfolio_value_long_call_positive():
    """
    A long call position has positive theoretical value.
    """

    response = client.post(
        VALUE_ENDPOINT,
        json=make_portfolio_request(
            [make_position(quantity=10)]
        ),
    )

    assert response.status_code == 200

    assert response.json()["portfolio_value"] > 0


def test_portfolio_value_short_call_negative():
    """
    A short call position has negative theoretical value.
    """

    response = client.post(
        VALUE_ENDPOINT,
        json=make_portfolio_request(
            [make_position(quantity=-10)]
        ),
    )

    assert response.status_code == 200

    assert response.json()["portfolio_value"] < 0


def test_portfolio_value_short_put_negative():
    """
    A short put position has negative theoretical value.
    """

    response = client.post(
        VALUE_ENDPOINT,
        json=make_portfolio_request(
            [
                make_position(
                    option_type="put",
                    quantity=-10,
                )
            ]
        ),
    )

    assert response.status_code == 200

    assert response.json()["portfolio_value"] < 0


def test_long_and_short_positions_cancel():
    """
    Identical long and short positions cancel exactly.
    """

    positions = [
        make_position(quantity=10),
        make_position(quantity=-10),
    ]

    response = client.post(
        VALUE_ENDPOINT,
        json=make_portfolio_request(positions),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["portfolio_value"] == pytest.approx(
        0.0,
        abs=1e-10,
    )

    assert data["net_contracts"] == 0


def test_portfolio_value_custom_multiplier():
    """
    Doubling the contract multiplier doubles position value.
    """

    standard = client.post(
        VALUE_ENDPOINT,
        json=make_portfolio_request(
            [make_position(multiplier=100)]
        ),
    )

    doubled = client.post(
        VALUE_ENDPOINT,
        json=make_portfolio_request(
            [make_position(multiplier=200)]
        ),
    )

    assert standard.status_code == 200
    assert doubled.status_code == 200

    assert doubled.json()["portfolio_value"] == pytest.approx(
        2 * standard.json()["portfolio_value"],
    )


def test_portfolio_value_expired_call():
    """
    Expired calls should use intrinsic value.
    """

    response = client.post(
        VALUE_ENDPOINT,
        json=make_portfolio_request(
            [
                make_position(
                    S=110.0,
                    K=100.0,
                    T=0.0,
                    quantity=3,
                )
            ]
        ),
    )

    assert response.status_code == 200

    assert response.json()["portfolio_value"] == pytest.approx(
        3000.0,
    )


def test_portfolio_value_zero_volatility():
    """
    The pricing engine must support sigma = 0.
    """

    response = client.post(
        VALUE_ENDPOINT,
        json=make_portfolio_request(
            [make_position(sigma=0.0)]
        ),
    )

    assert response.status_code == 200

    assert math.isfinite(
        response.json()["portfolio_value"]
    )


# ============================================================
# SECTION 2: PORTFOLIO GREEKS ENDPOINT
# ============================================================

def test_portfolio_greeks_success():
    """
    Verify successful aggregate Greek calculations.
    """

    response = client.post(
        GREEKS_ENDPOINT,
        json=make_portfolio_request(),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["position_count"] == 1

    assert "portfolio_value" in data
    assert "portfolio_delta" in data
    assert "portfolio_gamma" in data
    assert "portfolio_vega" in data
    assert "portfolio_theta" in data
    assert "portfolio_rho" in data


def test_portfolio_greeks_matches_domain_engine():
    """
    Compare API Greeks with the portfolio calculation engine.
    """

    positions = [
        make_position(),
        make_position(
            option_type="put",
            quantity=-5,
            K=95.0,
        ),
    ]

    response = client.post(
        GREEKS_ENDPOINT,
        json=make_portfolio_request(positions),
    )

    assert response.status_code == 200

    expected = make_domain_portfolio(
        positions
    ).calculate()

    actual = response.json()

    fields = [
        "portfolio_value",
        "portfolio_delta",
        "portfolio_gamma",
        "portfolio_vega",
        "portfolio_theta",
        "portfolio_rho",
    ]

    for field in fields:
        assert actual[field] == pytest.approx(
            expected[field],
        )


def test_portfolio_greeks_long_call_delta_positive():
    """
    Long calls have positive delta exposure.
    """

    response = client.post(
        GREEKS_ENDPOINT,
        json=make_portfolio_request(),
    )

    assert response.status_code == 200

    assert response.json()["portfolio_delta"] > 0


def test_portfolio_greeks_long_put_delta_negative():
    """
    Long puts have negative delta exposure.
    """

    response = client.post(
        GREEKS_ENDPOINT,
        json=make_portfolio_request(
            [make_position(option_type="put")]
        ),
    )

    assert response.status_code == 200

    assert response.json()["portfolio_delta"] < 0


def test_portfolio_greeks_short_call_delta_negative():
    """
    Short calls reverse the sign of delta exposure.
    """

    response = client.post(
        GREEKS_ENDPOINT,
        json=make_portfolio_request(
            [make_position(quantity=-10)]
        ),
    )

    assert response.status_code == 200

    assert response.json()["portfolio_delta"] < 0


def test_portfolio_greeks_long_call_gamma_positive():
    """
    Long vanilla options have nonnegative gamma.
    """

    response = client.post(
        GREEKS_ENDPOINT,
        json=make_portfolio_request(),
    )

    assert response.status_code == 200

    assert response.json()["portfolio_gamma"] > 0


def test_portfolio_greeks_short_call_gamma_negative():
    """
    Short vanilla options have nonpositive gamma exposure.
    """

    response = client.post(
        GREEKS_ENDPOINT,
        json=make_portfolio_request(
            [make_position(quantity=-10)]
        ),
    )

    assert response.status_code == 200

    assert response.json()["portfolio_gamma"] < 0


def test_portfolio_greeks_position_breakdown():
    """
    Each position should contain individual Greek contributions.
    """

    response = client.post(
        GREEKS_ENDPOINT,
        json=make_portfolio_request(),
    )

    assert response.status_code == 200

    position = response.json()["positions"][0]

    for field in (
        "delta",
        "gamma",
        "vega",
        "theta",
        "rho",
    ):
        assert field in position


def test_portfolio_greeks_expired_option():
    """
    Undefined Greeks should be JSON null.
    """

    response = client.post(
        GREEKS_ENDPOINT,
        json=make_portfolio_request(
            [make_position(T=0.0)]
        ),
    )

    assert response.status_code == 200

    position = response.json()["positions"][0]

    for field in (
        "delta",
        "gamma",
        "vega",
        "theta",
        "rho",
    ):
        assert position[field] is None


def test_portfolio_greeks_zero_volatility():
    """
    Zero-volatility options should not cause an API failure.
    """

    response = client.post(
        GREEKS_ENDPOINT,
        json=make_portfolio_request(
            [make_position(sigma=0.0)]
        ),
    )

    assert response.status_code == 200

    position = response.json()["positions"][0]

    assert position["gamma"] is None
    assert position["vega"] is None


def test_portfolio_greeks_and_value_agree():
    """
    Both portfolio endpoints must return the same valuation.
    """

    payload = make_portfolio_request(
        [
            make_position(),
            make_position(
                option_type="put",
                quantity=-5,
                K=95.0,
            ),
        ]
    )

    value_response = client.post(
        VALUE_ENDPOINT,
        json=payload,
    )

    greeks_response = client.post(
        GREEKS_ENDPOINT,
        json=payload,
    )

    assert value_response.status_code == 200
    assert greeks_response.status_code == 200

    assert value_response.json()[
        "portfolio_value"
    ] == pytest.approx(
        greeks_response.json()["portfolio_value"],
    )


# ============================================================
# SECTION 3: PORTFOLIO SCENARIO ENDPOINT
# ============================================================

def test_portfolio_scenarios_success():
    """
    Verify successful scenario analysis through FastAPI.
    """

    response = client.post(
        SCENARIOS_ENDPOINT,
        json=make_scenario_request(),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["scenario_count"] == 1
    assert data["position_count"] == 1

    assert len(data["scenarios"]) == 1


def test_scenario_no_change_zero_pnl():
    """
    No Change must produce zero theoretical P&L.
    """

    response = client.post(
        SCENARIOS_ENDPOINT,
        json=make_scenario_request(),
    )

    assert response.status_code == 200

    scenario = response.json()["scenarios"][0]

    assert scenario["scenario_pnl"] == pytest.approx(
        0.0,
        abs=1e-10,
    )


def test_scenario_baseline_matches_portfolio_value():
    """
    Scenario baseline must equal the valuation endpoint.
    """

    positions = [
        make_position(),
        make_position(
            option_type="put",
            quantity=-5,
            K=95.0,
        ),
    ]

    value_response = client.post(
        VALUE_ENDPOINT,
        json=make_portfolio_request(positions),
    )

    scenario_response = client.post(
        SCENARIOS_ENDPOINT,
        json=make_scenario_request(
            positions=positions,
        ),
    )

    assert value_response.status_code == 200
    assert scenario_response.status_code == 200

    assert scenario_response.json()[
        "original_portfolio_value"
    ] == pytest.approx(
        value_response.json()["portfolio_value"],
    )


def test_scenario_matches_domain_engine():
    """
    Compare API scenario results with the domain engine.
    """

    positions = [
        make_position(),
        make_position(
            option_type="put",
            quantity=-5,
            K=95.0,
        ),
    ]

    scenario = make_scenario(
        name="Market Decline",
        price_change_pct=-5.0,
        volatility_change=0.05,
        days_forward=7.0,
    )

    response = client.post(
        SCENARIOS_ENDPOINT,
        json=make_scenario_request(
            positions=positions,
            scenarios=[scenario],
        ),
    )

    assert response.status_code == 200

    portfolio = make_domain_portfolio(positions)

    analysis = PortfolioScenarioAnalysis(
        portfolio=portfolio,
        scenarios=[MarketScenario(**scenario)],
    )

    expected = analysis.calculate()

    actual = response.json()

    assert actual["original_portfolio_value"] == pytest.approx(
        expected["original_portfolio_value"],
    )

    assert actual["scenarios"][0][
        "scenario_pnl"
    ] == pytest.approx(
        expected["scenarios"][0]["scenario_pnl"],
    )


def test_scenario_market_rally_positive_call_pnl():
    """
    A long call should gain value when the stock rises.
    """

    response = client.post(
        SCENARIOS_ENDPOINT,
        json=make_scenario_request(
            scenarios=[
                make_scenario(
                    name="Market Rally",
                    price_change_pct=5.0,
                )
            ],
        ),
    )

    assert response.status_code == 200

    assert response.json()["scenarios"][0][
        "scenario_pnl"
    ] > 0


def test_scenario_market_decline_negative_call_pnl():
    """
    A long call should lose value when the stock declines.
    """

    response = client.post(
        SCENARIOS_ENDPOINT,
        json=make_scenario_request(
            scenarios=[
                make_scenario(
                    name="Market Decline",
                    price_change_pct=-5.0,
                )
            ],
        ),
    )

    assert response.status_code == 200

    assert response.json()["scenarios"][0][
        "scenario_pnl"
    ] < 0


def test_scenario_long_put_gains_from_decline():
    """
    A long put should gain value when the stock falls.
    """

    response = client.post(
        SCENARIOS_ENDPOINT,
        json=make_scenario_request(
            positions=[
                make_position(option_type="put")
            ],
            scenarios=[
                make_scenario(
                    name="Market Decline",
                    price_change_pct=-5.0,
                )
            ],
        ),
    )

    assert response.status_code == 200

    assert response.json()["scenarios"][0][
        "scenario_pnl"
    ] > 0


def test_scenario_short_call_loses_from_rally():
    """
    A short call should lose value when the stock rises.
    """

    response = client.post(
        SCENARIOS_ENDPOINT,
        json=make_scenario_request(
            positions=[
                make_position(quantity=-10)
            ],
            scenarios=[
                make_scenario(
                    name="Market Rally",
                    price_change_pct=5.0,
                )
            ],
        ),
    )

    assert response.status_code == 200

    assert response.json()["scenarios"][0][
        "scenario_pnl"
    ] < 0


def test_scenario_positive_volatility_shock():
    """
    Higher volatility should increase a long call's value.
    """

    response = client.post(
        SCENARIOS_ENDPOINT,
        json=make_scenario_request(
            scenarios=[
                make_scenario(
                    name="Volatility Increase",
                    volatility_change=0.05,
                )
            ],
        ),
    )

    assert response.status_code == 200

    assert response.json()["scenarios"][0][
        "scenario_pnl"
    ] > 0


def test_scenario_negative_volatility_shock():
    """
    Lower volatility should decrease a long call's value.
    """

    response = client.post(
        SCENARIOS_ENDPOINT,
        json=make_scenario_request(
            scenarios=[
                make_scenario(
                    name="Volatility Decrease",
                    volatility_change=-0.05,
                )
            ],
        ),
    )

    assert response.status_code == 200

    assert response.json()["scenarios"][0][
        "scenario_pnl"
    ] < 0


def test_scenario_time_decay():
    """
    An at-the-money long call should lose time value.
    """

    response = client.post(
        SCENARIOS_ENDPOINT,
        json=make_scenario_request(
            scenarios=[
                make_scenario(
                    name="Seven Days Forward",
                    days_forward=7.0,
                )
            ],
        ),
    )

    assert response.status_code == 200

    assert response.json()["scenarios"][0][
        "scenario_pnl"
    ] < 0


def test_scenario_expiration():
    """
    Options expiring during a scenario use intrinsic value.
    """

    response = client.post(
        SCENARIOS_ENDPOINT,
        json=make_scenario_request(
            positions=[
                make_position(
                    S=110.0,
                    K=100.0,
                    T=5.0 / 365.0,
                )
            ],
            scenarios=[
                make_scenario(
                    name="Expiration",
                    days_forward=10.0,
                )
            ],
        ),
    )

    assert response.status_code == 200

    position = response.json()["scenarios"][0][
        "positions"
    ][0]

    assert position["scenario_option_price"] == pytest.approx(
        10.0,
    )


def test_scenario_negative_volatility_returns_422():
    """
    A scenario producing negative volatility is invalid.
    """

    payload = make_scenario_request(
        scenarios=[
            make_scenario(
                name="Invalid Volatility",
                volatility_change=-0.30,
            )
        ],
    )

    assert_http_422(
        SCENARIOS_ENDPOINT,
        payload,
    )


def test_scenario_zero_volatility_allowed():
    """
    A shock that produces exactly zero volatility is valid.
    """

    response = client.post(
        SCENARIOS_ENDPOINT,
        json=make_scenario_request(
            scenarios=[
                make_scenario(
                    name="Zero Volatility",
                    volatility_change=-0.20,
                )
            ],
        ),
    )

    assert response.status_code == 200


def test_scenario_pnl_equals_value_difference():
    """
    P&L = shocked portfolio value - original portfolio value.
    """

    response = client.post(
        SCENARIOS_ENDPOINT,
        json=make_scenario_request(
            scenarios=[
                make_scenario(
                    name="Combined Shock",
                    price_change_pct=-5.0,
                    volatility_change=0.05,
                    days_forward=7.0,
                )
            ],
        ),
    )

    assert response.status_code == 200

    data = response.json()
    scenario = data["scenarios"][0]

    expected = (
        scenario["scenario_portfolio_value"]
        - data["original_portfolio_value"]
    )

    assert scenario["scenario_pnl"] == pytest.approx(
        expected,
        abs=1e-8,
    )


def test_scenario_pnl_equals_position_pnl_sum():
    """
    Portfolio P&L must equal the sum of position P&L.
    """

    positions = [
        make_position(),
        make_position(
            option_type="put",
            quantity=-5,
            K=95.0,
        ),
    ]

    response = client.post(
        SCENARIOS_ENDPOINT,
        json=make_scenario_request(
            positions=positions,
            scenarios=[
                make_scenario(
                    name="Combined Shock",
                    price_change_pct=-5.0,
                    volatility_change=0.05,
                    days_forward=7.0,
                )
            ],
        ),
    )

    assert response.status_code == 200

    scenario = response.json()["scenarios"][0]

    expected = sum(
        position["position_pnl"]
        for position in scenario["positions"]
    )

    assert scenario["scenario_pnl"] == pytest.approx(
        expected,
        abs=1e-8,
    )


def test_scenario_zero_baseline_return_is_null():
    """
    Percentage return is undefined for a zero-value portfolio.
    """

    positions = [
        make_position(quantity=10),
        make_position(quantity=-10),
    ]

    response = client.post(
        SCENARIOS_ENDPOINT,
        json=make_scenario_request(
            positions=positions,
            scenarios=[
                make_scenario(
                    name="Market Rally",
                    price_change_pct=5.0,
                )
            ],
        ),
    )

    assert response.status_code == 200

    assert response.json()["scenarios"][0][
        "scenario_return_pct"
    ] is None


def test_multiple_scenarios_preserve_order():
    """
    Scenario responses must preserve request order.
    """

    scenarios = [
        make_scenario(
            name="Crash",
            price_change_pct=-10.0,
        ),
        make_scenario(
            name="Base",
        ),
        make_scenario(
            name="Rally",
            price_change_pct=10.0,
        ),
    ]

    response = client.post(
        SCENARIOS_ENDPOINT,
        json=make_scenario_request(
            scenarios=scenarios,
        ),
    )

    assert response.status_code == 200

    names = [
        scenario["name"]
        for scenario in response.json()["scenarios"]
    ]

    assert names == [
        "Crash",
        "Base",
        "Rally",
    ]


# ============================================================
# SECTION 4: PORTFOLIO REQUEST VALIDATION
# ============================================================

@pytest.mark.parametrize(
    "endpoint",
    [
        VALUE_ENDPOINT,
        GREEKS_ENDPOINT,
        SCENARIOS_ENDPOINT,
    ],
)
def test_empty_positions_rejected(endpoint):
    """
    Every portfolio endpoint requires at least one position.
    """

    payload = make_portfolio_request(positions=[])

    if endpoint == SCENARIOS_ENDPOINT:
        payload["scenarios"] = [make_scenario()]

    assert_http_422(endpoint, payload)


@pytest.mark.parametrize(
    "endpoint",
    [
        VALUE_ENDPOINT,
        GREEKS_ENDPOINT,
        SCENARIOS_ENDPOINT,
    ],
)
def test_missing_positions_rejected(endpoint):
    """
    The positions field is required.
    """

    payload = {}

    if endpoint == SCENARIOS_ENDPOINT:
        payload["scenarios"] = [make_scenario()]

    assert_http_422(endpoint, payload)


@pytest.mark.parametrize(
    "endpoint",
    [
        VALUE_ENDPOINT,
        GREEKS_ENDPOINT,
        SCENARIOS_ENDPOINT,
    ],
)
def test_extra_top_level_field_rejected(endpoint):
    """
    Unexpected top-level request fields are forbidden.
    """

    payload = make_portfolio_request()

    if endpoint == SCENARIOS_ENDPOINT:
        payload["scenarios"] = [make_scenario()]

    payload["unexpected"] = 123

    assert_http_422(endpoint, payload)


@pytest.mark.parametrize(
    "option_type",
    [
        "CALL",
        "PUT",
        "invalid",
        "",
        "Call",
    ],
)
def test_invalid_option_type_rejected(option_type):
    """
    Only lowercase call and put are accepted.
    """

    payload = make_portfolio_request(
        [make_position(option_type=option_type)]
    )

    assert_http_422(
        VALUE_ENDPOINT,
        payload,
    )


@pytest.mark.parametrize(
    "quantity",
    [
        0,
        1.5,
        "10",
        True,
        None,
    ],
)
def test_invalid_quantity_rejected(quantity):
    """
    Quantity must be a nonzero strict integer.
    """

    payload = make_portfolio_request(
        [make_position(quantity=quantity)]
    )

    assert_http_422(
        VALUE_ENDPOINT,
        payload,
    )


@pytest.mark.parametrize(
    "multiplier",
    [
        0,
        -1,
        1.5,
        "100",
        True,
        None,
    ],
)
def test_invalid_multiplier_rejected(multiplier):
    """
    Multiplier must be a positive strict integer.
    """

    payload = make_portfolio_request(
        [make_position(multiplier=multiplier)]
    )

    assert_http_422(
        VALUE_ENDPOINT,
        payload,
    )


@pytest.mark.parametrize(
    "field,invalid_value",
    [
        ("S", 0),
        ("S", -100),
        ("K", 0),
        ("K", -100),
        ("T", -1),
        ("sigma", -0.1),
        ("r", float("inf")),
        ("q", float("-inf")),
        ("sigma", float("nan")),
    ],
)
def test_invalid_financial_parameters_rejected(
    field,
    invalid_value,
):
    """
    Invalid financial inputs must produce HTTP 422.
    """

    payload = make_portfolio_request(
        [make_position(**{field: invalid_value})]
    )

    assert_http_422(
        VALUE_ENDPOINT,
        payload,
    )


def test_mismatched_underlying_prices_rejected():
    """
    All positions must use the same underlying price.
    """

    payload = make_portfolio_request(
        [
            make_position(S=100.0),
            make_position(S=101.0),
        ]
    )

    assert_http_422(
        VALUE_ENDPOINT,
        payload,
    )


def test_extra_position_field_rejected():
    """
    Unexpected fields inside a position are forbidden.
    """

    payload = make_portfolio_request(
        [
            make_position(
                unexpected_parameter=123,
            )
        ]
    )

    assert_http_422(
        VALUE_ENDPOINT,
        payload,
    )


def test_more_than_10000_positions_rejected():
    """
    Portfolio requests cannot exceed 10,000 positions.
    """

    positions = [
        make_position()
        for _ in range(10_001)
    ]

    payload = make_portfolio_request(
        positions=positions,
    )

    assert_http_422(
        VALUE_ENDPOINT,
        payload,
    )


# ============================================================
# SECTION 5: SCENARIO REQUEST VALIDATION
# ============================================================

def test_empty_scenarios_rejected():
    """
    Scenario analysis requires at least one scenario.
    """

    payload = make_scenario_request(
        scenarios=[],
    )

    assert_http_422(
        SCENARIOS_ENDPOINT,
        payload,
    )


def test_missing_scenarios_rejected():
    """
    The scenarios field is required.
    """

    payload = make_portfolio_request()

    assert_http_422(
        SCENARIOS_ENDPOINT,
        payload,
    )


def test_duplicate_scenario_names_rejected():
    """
    Duplicate scenario names are forbidden.
    """

    payload = make_scenario_request(
        scenarios=[
            make_scenario(name="Duplicate"),
            make_scenario(name="Duplicate"),
        ],
    )

    assert_http_422(
        SCENARIOS_ENDPOINT,
        payload,
    )


@pytest.mark.parametrize(
    "name",
    [
        "",
        "   ",
        "\t",
        "\n",
    ],
)
def test_blank_scenario_name_rejected(name):
    """
    Scenario names cannot be empty or whitespace-only.
    """

    payload = make_scenario_request(
        scenarios=[
            make_scenario(name=name)
        ],
    )

    assert_http_422(
        SCENARIOS_ENDPOINT,
        payload,
    )


@pytest.mark.parametrize(
    "price_change_pct",
    [
        -100.0,
        -101.0,
        -200.0,
    ],
)
def test_invalid_price_shock_rejected(price_change_pct):
    """
    A stock-price decline of 100% or more is invalid.
    """

    payload = make_scenario_request(
        scenarios=[
            make_scenario(
                price_change_pct=price_change_pct,
            )
        ],
    )

    assert_http_422(
        SCENARIOS_ENDPOINT,
        payload,
    )


@pytest.mark.parametrize(
    "days_forward",
    [
        -1,
        -7,
        -365,
    ],
)
def test_negative_days_forward_rejected(days_forward):
    """
    Scenario time advancement cannot be negative.
    """

    payload = make_scenario_request(
        scenarios=[
            make_scenario(
                days_forward=days_forward,
            )
        ],
    )

    assert_http_422(
        SCENARIOS_ENDPOINT,
        payload,
    )


@pytest.mark.parametrize(
    "field",
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
    ],
)
def test_nonfinite_scenario_values_rejected(
    field,
    invalid_value,
):
    """
    Scenario parameters must be finite numbers.
    """

    payload = make_scenario_request(
        scenarios=[
            make_scenario(
                **{field: invalid_value}
            )
        ],
    )

    assert_http_422(
        SCENARIOS_ENDPOINT,
        payload,
    )


def test_extra_scenario_field_rejected():
    """
    Unexpected scenario fields are forbidden.
    """

    payload = make_scenario_request(
        scenarios=[
            make_scenario(
                unexpected_field=123,
            )
        ],
    )

    assert_http_422(
        SCENARIOS_ENDPOINT,
        payload,
    )


def test_more_than_100_scenarios_rejected():
    """
    Scenario requests cannot exceed 100 scenarios.
    """

    scenarios = [
        make_scenario(
            name=f"Scenario {index}"
        )
        for index in range(101)
    ]

    payload = make_scenario_request(
        scenarios=scenarios,
    )

    assert_http_422(
        SCENARIOS_ENDPOINT,
        payload,
    )


# ============================================================
# SECTION 6: RESPONSE STRUCTURE AND CONSISTENCY
# ============================================================

def test_value_response_contains_expected_fields():
    """
    Verify the valuation endpoint's response structure.
    """

    response = client.post(
        VALUE_ENDPOINT,
        json=make_portfolio_request(),
    )

    assert response.status_code == 200

    data = response.json()

    expected_fields = {
        "position_count",
        "total_contracts",
        "net_contracts",
        "portfolio_value",
        "positions",
    }

    assert expected_fields.issubset(data)


def test_greeks_response_contains_expected_fields():
    """
    Verify the aggregate Greeks response structure.
    """

    response = client.post(
        GREEKS_ENDPOINT,
        json=make_portfolio_request(),
    )

    assert response.status_code == 200

    data = response.json()

    expected_fields = {
        "position_count",
        "total_contracts",
        "net_contracts",
        "portfolio_value",
        "portfolio_delta",
        "portfolio_gamma",
        "portfolio_vega",
        "portfolio_theta",
        "portfolio_rho",
        "positions",
    }

    assert expected_fields.issubset(data)


def test_scenario_response_contains_expected_fields():
    """
    Verify the scenario response structure.
    """

    response = client.post(
        SCENARIOS_ENDPOINT,
        json=make_scenario_request(),
    )

    assert response.status_code == 200

    data = response.json()

    expected_fields = {
        "original_portfolio_value",
        "scenario_count",
        "position_count",
        "scenarios",
    }

    assert expected_fields.issubset(data)


def test_scenario_position_breakdown_fields():
    """
    Verify that scenario positions contain the expected values.
    """

    response = client.post(
        SCENARIOS_ENDPOINT,
        json=make_scenario_request(),
    )

    assert response.status_code == 200

    position = response.json()["scenarios"][0]["positions"][0]

    expected_fields = {
        "position_index",
        "option_type",
        "quantity",
        "multiplier",
        "original_option_price",
        "scenario_option_price",
        "original_position_value",
        "scenario_position_value",
        "position_pnl",
    }

    assert expected_fields.issubset(position)


def test_portfolio_api_routes_registered():
    """
    Verify all three portfolio endpoints exist.
    """

    paths = {
        route.path
        for route in app.routes
    }

    assert VALUE_ENDPOINT in paths
    assert GREEKS_ENDPOINT in paths
    assert SCENARIOS_ENDPOINT in paths


def test_api_version_updated():
    """
    Verify the portfolio integration release version.
    """

    assert app.version == "1.3.0"