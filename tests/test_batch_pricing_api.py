"""
Tests for the vectorized batch-pricing API.

These tests verify:
- Correct call and put prices.
- Agreement with the original Black-Scholes engine.
- Preservation of input order.
- Expired and zero-volatility options.
- Request validation.
- Minimum and maximum batch sizes.
- Consistency with the existing single-option API.

Run with:

    python -m pytest tests/test_batch_pricing_api.py -v
"""

import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.pricing.black_scholes import BlackScholes

# Create a test client that sends requests directly to FastAPI.
# No running server or internet connection is required.
client = TestClient(app)

# The endpoint we're testing.
BATCH_URL = "/api/v1/options/batch-price"

# The original single-option endpoint.
SINGLE_URL = "/api/v1/options/price"


def make_option(
    S=100.0,
    K=100.0,
    T=1.0,
    r=0.05,
    sigma=0.2,
    q=0.0,
):
    """Create a valid option contract for API testing."""

    return {
        "S": S,
        "K": K,
        "T": T,
        "r": r,
        "sigma": sigma,
        "q": q,
    }


def post_batch(options):
    """Send an options batch to the API."""

    return client.post(
        BATCH_URL,
        json={"options": options},
    )


# ============================================================
# BASIC FUNCTIONALITY
# ============================================================


def test_batch_endpoint_exists():
    """The new endpoint should accept a valid request."""

    response = post_batch([make_option()])

    assert response.status_code == 200


def test_batch_response_structure():
    """The response should contain count and results."""

    response = post_batch(
        [
            make_option(K=90),
            make_option(K=100),
            make_option(K=110),
        ]
    )

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 3
    assert len(data["results"]) == 3

    for result in data["results"]:
        assert "call_price" in result
        assert "put_price" in result


def test_batch_single_option():
    """A batch containing one option should price correctly."""

    option = make_option()

    response = post_batch([option])

    assert response.status_code == 200

    result = response.json()["results"][0]

    engine = BlackScholes(**option)

    assert result["call_price"] == pytest.approx(
        engine.call_price(),
        abs=1e-4,
    )

    assert result["put_price"] == pytest.approx(
        engine.put_price(),
        abs=1e-4,
    )


def test_batch_multiple_options():
    """Batch prices should agree with scalar pricing."""

    options = [
        make_option(K=80),
        make_option(K=90),
        make_option(K=100),
        make_option(K=110),
        make_option(K=120),
    ]

    response = post_batch(options)

    assert response.status_code == 200

    results = response.json()["results"]

    for option, result in zip(options, results, strict=True):
        engine = BlackScholes(**option)

        assert result["call_price"] == pytest.approx(
            engine.call_price(),
            abs=1e-4,
        )

        assert result["put_price"] == pytest.approx(
            engine.put_price(),
            abs=1e-4,
        )


def test_batch_preserves_input_order():
    """Returned prices must correspond to the original order."""

    options = [
        make_option(K=120),
        make_option(K=80),
        make_option(K=110),
        make_option(K=90),
        make_option(K=100),
    ]

    response = post_batch(options)

    assert response.status_code == 200

    results = response.json()["results"]

    for option, result in zip(options, results, strict=True):
        engine = BlackScholes(**option)

        assert result["call_price"] == pytest.approx(
            engine.call_price(),
            abs=1e-4,
        )


# ============================================================
# FINANCIAL EDGE CASES
# ============================================================


def test_batch_expired_options():
    """Expired options should return their intrinsic values."""

    options = [
        make_option(S=120, K=100, T=0),
        make_option(S=80, K=100, T=0),
        make_option(S=100, K=100, T=0),
    ]

    response = post_batch(options)

    assert response.status_code == 200

    results = response.json()["results"]

    assert results[0] == {
        "call_price": 20.0,
        "put_price": 0.0,
    }

    assert results[1] == {
        "call_price": 0.0,
        "put_price": 20.0,
    }

    assert results[2] == {
        "call_price": 0.0,
        "put_price": 0.0,
    }


def test_batch_zero_volatility():
    """Zero-volatility options should match scalar pricing."""

    options = [
        make_option(K=80, sigma=0),
        make_option(K=100, sigma=0),
        make_option(K=120, sigma=0),
    ]

    response = post_batch(options)

    assert response.status_code == 200

    results = response.json()["results"]

    for option, result in zip(options, results, strict=True):
        engine = BlackScholes(**option)

        assert result["call_price"] == pytest.approx(
            engine.call_price(),
            abs=1e-4,
        )

        assert result["put_price"] == pytest.approx(
            engine.put_price(),
            abs=1e-4,
        )


def test_batch_mixed_edge_cases():
    """A single batch may contain different pricing scenarios."""

    options = [
        make_option(),
        make_option(T=0),
        make_option(sigma=0),
        make_option(r=-0.01),
        make_option(q=0.03),
    ]

    response = post_batch(options)

    assert response.status_code == 200

    results = response.json()["results"]

    for option, result in zip(options, results, strict=True):
        engine = BlackScholes(**option)

        assert result["call_price"] == pytest.approx(
            engine.call_price(),
            abs=1e-4,
        )

        assert result["put_price"] == pytest.approx(
            engine.put_price(),
            abs=1e-4,
        )


def test_batch_default_dividend_yield():
    """Omitting q should use the default dividend yield of zero."""

    option = make_option()

    del option["q"]

    response = post_batch([option])

    assert response.status_code == 200

    result = response.json()["results"][0]

    engine = BlackScholes(**option)

    assert result["call_price"] == pytest.approx(
        engine.call_price(),
        abs=1e-4,
    )


# ============================================================
# API CONSISTENCY
# ============================================================


def test_batch_matches_single_endpoint():
    """Batch and single-option endpoints should return equal prices."""

    options = [
        make_option(K=90),
        make_option(K=100),
        make_option(K=110),
    ]

    batch_response = post_batch(options)

    assert batch_response.status_code == 200

    batch_results = batch_response.json()["results"]

    for option, batch_result in zip(
        options,
        batch_results,
        strict=True,
    ):
        single_response = client.post(
            SINGLE_URL,
            json=option,
        )

        assert single_response.status_code == 200

        assert batch_result == single_response.json()


# ============================================================
# REQUEST VALIDATION
# ============================================================


def test_batch_rejects_empty_list():
    """At least one option must be provided."""

    response = post_batch([])

    assert response.status_code == 422


def test_batch_rejects_missing_options():
    """The outer request must contain the options field."""

    response = client.post(
        BATCH_URL,
        json={},
    )

    assert response.status_code == 422


def test_batch_rejects_extra_outer_fields():
    """Unexpected fields in the batch request are rejected."""

    response = client.post(
        BATCH_URL,
        json={
            "options": [make_option()],
            "unexpected": True,
        },
    )

    assert response.status_code == 422


def test_batch_rejects_extra_option_fields():
    """Unexpected fields inside an option are rejected."""

    option = make_option()
    option["unexpected"] = 123

    response = post_batch([option])

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("S", 0),
        ("S", -100),
        ("K", 0),
        ("K", -100),
        ("T", -1),
        ("sigma", -0.2),
        ("r", "invalid"),
        ("q", "invalid"),
        ("S", None),
        ("K", None),
        ("T", None),
        ("sigma", None),
    ],
)
def test_batch_rejects_invalid_parameters(field, invalid_value):
    """Invalid financial parameters should produce HTTP 422."""

    option = make_option()
    option[field] = invalid_value

    response = post_batch([option])

    assert response.status_code == 422


@pytest.mark.parametrize(
    "field",
    ["S", "K", "T", "r", "sigma"],
)
def test_batch_rejects_missing_required_parameters(field):
    """Required option fields must be present."""

    option = make_option()
    del option[field]

    response = post_batch([option])

    assert response.status_code == 422


def test_batch_rejects_invalid_option_in_middle():
    """One invalid contract should reject the entire batch."""

    options = [
        make_option(K=90),
        make_option(K=-100),
        make_option(K=110),
    ]

    response = post_batch(options)

    assert response.status_code == 422


def test_batch_rejects_wrong_options_type():
    """The options field must be a list."""

    response = client.post(
        BATCH_URL,
        json={"options": "not a list"},
    )

    assert response.status_code == 422


# ============================================================
# BATCH SIZE LIMITS
# ============================================================


def test_batch_accepts_maximum_size():
    """Exactly 10,000 contracts should be accepted."""

    options = [make_option()] * 10_000

    response = post_batch(options)

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 10_000
    assert len(data["results"]) == 10_000


def test_batch_rejects_excessive_size():
    """More than 10,000 contracts should be rejected."""

    options = [make_option()] * 10_001

    response = post_batch(options)

    assert response.status_code == 422


# ============================================================
# RESPONSE ACCURACY
# ============================================================


def test_batch_prices_are_nonnegative():
    """Call and put prices should not be negative."""

    options = [
        make_option(K=50),
        make_option(K=100),
        make_option(K=150),
    ]

    response = post_batch(options)

    assert response.status_code == 200

    for result in response.json()["results"]:
        assert result["call_price"] >= 0
        assert result["put_price"] >= 0


def test_batch_prices_have_four_decimal_precision():
    """Prices should be rounded to four decimal places."""

    response = post_batch([make_option()])

    assert response.status_code == 200

    result = response.json()["results"][0]

    assert result["call_price"] == round(
        result["call_price"],
        4,
    )

    assert result["put_price"] == round(
        result["put_price"],
        4,
    )