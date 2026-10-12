"""
Automated tests for the FastAPI batch Greeks endpoint.

Tests cover:

- Successful API requests
- Correct response structure
- Numerical consistency with scalar Black-Scholes
- Numerical consistency with the single-option Greeks API
- Contract ordering
- Dividend yields
- Expired options
- Zero-volatility options
- Invalid financial parameters
- Request size limits
- Unknown request fields
- Large batch processing

Run:

    python -m pytest tests/test_batch_greeks_api.py -v
"""

import math

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.pricing.black_scholes import BlackScholes

# ============================================================
# TEST CLIENT
# ============================================================

# TestClient allows us to send HTTP-style requests to
# FastAPI without starting a separate web server.
client = TestClient(app)


# ============================================================
# ENDPOINT CONFIGURATION
# ============================================================

BATCH_GREEKS_URL = "/api/v1/options/batch-greeks"
SINGLE_GREEKS_URL = "/api/v1/options/greeks"

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
# TEST DATA
# ============================================================

def make_option(
    S=100.0,
    K=100.0,
    T=1.0,
    r=0.05,
    sigma=0.20,
    q=0.0,
):
    """Create a valid option request with customizable values."""

    return {
        "S": S,
        "K": K,
        "T": T,
        "r": r,
        "sigma": sigma,
        "q": q,
    }


# ============================================================
# BASIC API FUNCTIONALITY
# ============================================================

def test_batch_greeks_returns_http_200():
    """A valid request should succeed."""

    response = client.post(
        BATCH_GREEKS_URL,
        json={"options": [make_option()]},
    )

    assert response.status_code == 200


def test_batch_greeks_response_structure():
    """Verify the response contains count and results."""

    response = client.post(
        BATCH_GREEKS_URL,
        json={"options": [make_option()]},
    )

    data = response.json()

    assert set(data) == {"count", "results"}
    assert data["count"] == 1
    assert len(data["results"]) == 1


def test_batch_greeks_returns_all_fields():
    """Every result should contain all ten expected outputs."""

    response = client.post(
        BATCH_GREEKS_URL,
        json={"options": [make_option()]},
    )

    result = response.json()["results"][0]

    assert set(result) == set(EXPECTED_FIELDS)


def test_batch_greeks_multiple_contracts():
    """Verify that multiple contracts can be processed."""

    options = [
        make_option(K=90),
        make_option(K=100),
        make_option(K=110),
    ]

    response = client.post(
        BATCH_GREEKS_URL,
        json={"options": options},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 3
    assert len(data["results"]) == 3


# ============================================================
# NUMERICAL CONSISTENCY
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
    ],
)
def test_batch_greeks_matches_scalar_engine(
    S,
    K,
    T,
    r,
    sigma,
    q,
):
    """Verify that batch results match the original scalar engine."""

    option = make_option(
        S=S,
        K=K,
        T=T,
        r=r,
        sigma=sigma,
        q=q,
    )

    expected = BlackScholes(**option).greeks()

    response = client.post(
        BATCH_GREEKS_URL,
        json={"options": [option]},
    )

    assert response.status_code == 200

    actual = response.json()["results"][0]

    for field in EXPECTED_FIELDS:

        assert actual[field] == pytest.approx(
            expected[field],
            abs=1e-4,
        )


def test_batch_greeks_matches_single_greeks_endpoint():
    """Verify consistency with the existing single-option API."""

    option = make_option(
        S=125,
        K=110,
        T=0.75,
        r=0.04,
        sigma=0.30,
        q=0.02,
    )

    single_response = client.post(
        SINGLE_GREEKS_URL,
        json=option,
    )

    batch_response = client.post(
        BATCH_GREEKS_URL,
        json={"options": [option]},
    )

    assert single_response.status_code == 200
    assert batch_response.status_code == 200

    assert (
        batch_response.json()["results"][0]
        == single_response.json()
    )


def test_batch_greeks_preserves_contract_order():
    """Verify that results correspond to the submitted order."""

    options = [
        make_option(K=90),
        make_option(K=100),
        make_option(K=110),
    ]

    response = client.post(
        BATCH_GREEKS_URL,
        json={"options": options},
    )

    results = response.json()["results"]

    # Increasing strike prices should reduce call prices.
    assert (
        results[0]["call_price"]
        > results[1]["call_price"]
        > results[2]["call_price"]
    )


def test_batch_greeks_supports_default_dividend_yield():
    """Verify that q defaults to zero when omitted."""

    option = make_option()
    option.pop("q")

    response = client.post(
        BATCH_GREEKS_URL,
        json={"options": [option]},
    )

    assert response.status_code == 200

    expected = BlackScholes(**option).greeks()

    assert response.json()["results"][0] == expected


def test_batch_greeks_supports_nonzero_dividend_yield():
    """Verify that continuous dividends affect the Greeks."""

    option = make_option(q=0.03)

    response = client.post(
        BATCH_GREEKS_URL,
        json={"options": [option]},
    )

    assert response.status_code == 200

    expected = BlackScholes(**option).greeks()

    assert response.json()["results"][0] == expected


# ============================================================
# EDGE CASES
# ============================================================

def test_batch_greeks_expired_option():
    """Expired contracts should have valid prices and null Greeks."""

    option = make_option(
        S=110,
        K=100,
        T=0,
        sigma=0.2,
    )

    response = client.post(
        BATCH_GREEKS_URL,
        json={"options": [option]},
    )

    assert response.status_code == 200

    result = response.json()["results"][0]

    assert result["call_price"] == 10.0
    assert result["put_price"] == 0.0

    for field in EXPECTED_FIELDS[2:]:
        assert result[field] is None


def test_batch_greeks_zero_volatility():
    """Zero-volatility contracts should have null Greeks."""

    option = make_option(
        T=1,
        sigma=0,
    )

    response = client.post(
        BATCH_GREEKS_URL,
        json={"options": [option]},
    )

    assert response.status_code == 200

    result = response.json()["results"][0]

    assert math.isfinite(result["call_price"])
    assert math.isfinite(result["put_price"])

    for field in EXPECTED_FIELDS[2:]:
        assert result[field] is None


def test_batch_greeks_mixed_edge_cases():
    """Verify mixed valid and undefined-Greek contracts."""

    options = [
        make_option(),
        make_option(T=0),
        make_option(sigma=0),
    ]

    response = client.post(
        BATCH_GREEKS_URL,
        json={"options": options},
    )

    assert response.status_code == 200

    results = response.json()["results"]

    assert results[0]["call_delta"] is not None
    assert results[1]["call_delta"] is None
    assert results[2]["call_delta"] is None


# ============================================================
# INPUT VALIDATION
# ============================================================

@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("S", 0),
        ("S", -100),
        ("K", 0),
        ("K", -100),
        ("T", -1),
        ("sigma", -0.2),
        ("S", None),
        ("K", None),
        ("T", None),
        ("r", None),
        ("sigma", None),
        ("q", None),
        ("S", "invalid"),
        ("K", "invalid"),
        ("T", "invalid"),
        ("r", "invalid"),
        ("sigma", "invalid"),
        ("q", "invalid"),
    ],
)
def test_batch_greeks_rejects_invalid_fields(field, value):
    """Invalid contract fields should produce HTTP 422."""

    option = make_option()
    option[field] = value

    response = client.post(
        BATCH_GREEKS_URL,
        json={"options": [option]},
    )

    assert response.status_code == 422


def test_batch_greeks_rejects_unknown_contract_field():
    """Unexpected fields inside a contract should be rejected."""

    option = make_option()
    option["unknown_field"] = 123

    response = client.post(
        BATCH_GREEKS_URL,
        json={"options": [option]},
    )

    assert response.status_code == 422


def test_batch_greeks_rejects_unknown_outer_field():
    """Unexpected fields outside the options list should be rejected."""

    response = client.post(
        BATCH_GREEKS_URL,
        json={
            "options": [make_option()],
            "unknown_field": 123,
        },
    )

    assert response.status_code == 422


def test_batch_greeks_rejects_missing_options():
    """The options field is required."""

    response = client.post(
        BATCH_GREEKS_URL,
        json={},
    )

    assert response.status_code == 422


def test_batch_greeks_rejects_empty_batch():
    """At least one contract must be supplied."""

    response = client.post(
        BATCH_GREEKS_URL,
        json={"options": []},
    )

    assert response.status_code == 422


def test_batch_greeks_rejects_too_many_contracts():
    """Requests containing more than 10,000 contracts are rejected."""

    options = [make_option()] * 10_001

    response = client.post(
        BATCH_GREEKS_URL,
        json={"options": options},
    )

    assert response.status_code == 422


def test_batch_greeks_accepts_maximum_batch_size():
    """Verify that exactly 10,000 contracts are accepted."""

    options = [make_option()] * 10_000

    response = client.post(
        BATCH_GREEKS_URL,
        json={"options": options},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 10_000
    assert len(data["results"]) == 10_000


def test_batch_greeks_rejects_invalid_contract_in_batch():
    """One invalid contract should reject the entire batch."""

    options = [
        make_option(),
        make_option(K=-100),
        make_option(),
    ]

    response = client.post(
        BATCH_GREEKS_URL,
        json={"options": options},
    )

    assert response.status_code == 422


# ============================================================
# RESPONSE PRECISION
# ============================================================

def test_batch_greeks_returns_finite_values():
    """All defined outputs should contain finite numbers."""

    response = client.post(
        BATCH_GREEKS_URL,
        json={"options": [make_option()]},
    )

    result = response.json()["results"][0]

    for field in EXPECTED_FIELDS:

        assert isinstance(result[field], (int, float))
        assert math.isfinite(result[field])


def test_batch_greeks_rounds_to_four_decimals():
    """Verify the same four-decimal convention as the scalar engine."""

    response = client.post(
        BATCH_GREEKS_URL,
        json={"options": [make_option()]},
    )

    result = response.json()["results"][0]

    for field in EXPECTED_FIELDS:

        value = result[field]

        assert value == round(value, 4)


# ============================================================
# API METADATA
# ============================================================

def test_batch_greeks_appears_in_openapi():
    """Verify that FastAPI documents the new endpoint."""

    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert BATCH_GREEKS_URL in paths
    assert "post" in paths[BATCH_GREEKS_URL]