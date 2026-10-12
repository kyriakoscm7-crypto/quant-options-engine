from unittest.mock import patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.api.main import app

# Create a test client that sends simulated HTTP requests
# directly to our FastAPI application.
client = TestClient(app)


# Standard option parameters used throughout our tests.
VALID_OPTION = {
    "S": 100,
    "K": 100,
    "T": 1,
    "r": 0.05,
    "sigma": 0.20,
    "q": 0
}


# TEST 1: Verify that the health endpoint works.
def test_health_check():

    response = client.get("/health")

    assert response.status_code == 200

    assert response.json()["status"] == "healthy"


# TEST 2: Verify that the pricing endpoint
# returns the expected Black-Scholes prices.
def test_option_pricing():

    response = client.post(
        "/api/v1/options/price",
        json=VALID_OPTION
    )

    assert response.status_code == 200

    data = response.json()

    assert data["call_price"] == pytest.approx(10.4506)
    assert data["put_price"] == pytest.approx(5.5735)


# TEST 3: Verify that the Greeks endpoint
# returns the expected risk sensitivities.
def test_option_greeks():

    response = client.post(
        "/api/v1/options/greeks",
        json=VALID_OPTION
    )

    assert response.status_code == 200

    data = response.json()

    assert data["call_delta"] == pytest.approx(0.6368)
    assert data["put_delta"] == pytest.approx(-0.3632)
    assert data["gamma"] == pytest.approx(0.0188)
    assert data["vega"] == pytest.approx(0.3752)


# TEST 4: Verify that the IV endpoint
# recovers the correct implied volatility.
def test_implied_volatility_endpoint():

    request_data = {
        "market_price": 10.4505835722,
        "S": 100,
        "K": 100,
        "T": 1,
        "r": 0.05,
        "option_type": "call",
        "q": 0
    }

    response = client.post(
        "/api/v1/options/implied-volatility",
        json=request_data
    )

    assert response.status_code == 200

    data = response.json()

    assert data["implied_volatility"] == pytest.approx(0.20)
    assert data["implied_volatility_percent"] == pytest.approx(20.0)


# TEST 5: Negative stock prices should be rejected.
def test_invalid_stock_price():

    invalid_option = VALID_OPTION.copy()

    invalid_option["S"] = -100

    response = client.post(
        "/api/v1/options/price",
        json=invalid_option
    )

    assert response.status_code == 422


# TEST 6: Missing required parameters should be rejected.
def test_missing_parameters():

    response = client.post(
        "/api/v1/options/price",
        json={"S": 100}
    )

    assert response.status_code == 422


# TEST 7: Invalid option types should be rejected.
def test_invalid_option_type():

    request_data = {
        "market_price": 10,
        "S": 100,
        "K": 100,
        "T": 1,
        "r": 0.05,
        "option_type": "invalid"
    }

    response = client.post(
        "/api/v1/options/implied-volatility",
        json=request_data
    )

    assert response.status_code == 422


# TEST 8: Market prices outside theoretical bounds
# should produce an HTTP 422 response.
def test_invalid_market_price():

    request_data = {
        "market_price": 150,
        "S": 100,
        "K": 100,
        "T": 1,
        "r": 0.05,
        "option_type": "call"
    }

    response = client.post(
        "/api/v1/options/implied-volatility",
        json=request_data
    )

    assert response.status_code == 422


    # TEST 9:
# Verify the market-data API returns correctly formatted results.
def test_market_data_endpoint():

    # Create predictable market data without contacting Yahoo Finance.
    mock_data = pd.DataFrame([
        {
            "Ticker": "SPY",
            "Expiration": "2026-10-19",
            "Strike": 780.0,
            "Bid": 5.0,
            "Ask": 5.2,
            "MidPrice": 5.1,
            "ImpliedVolatility": 20.5,
            "TimeToExpiration": 0.019
        }
    ])

    # Replace the real Yahoo Finance function during this test.
    with patch(
        "app.api.main.fetch_option_chain",
        return_value=mock_data
    ):

        response = client.get(
            "/api/v1/market/options/SPY"
        )

    assert response.status_code == 200

    data = response.json()

    assert data["ticker"] == "SPY"
    assert data["count"] == 1
    assert len(data["options"]) == 1
    assert data["options"][0]["Strike"] == 780.0


# TEST 10:
# Verify invalid ticker symbols are rejected.
def test_invalid_ticker():

    response = client.get(
        "/api/v1/market/options/INVALID!"
    )

    assert response.status_code == 422


# TEST 11:
# Verify provider failures return HTTP 503.
def test_market_data_failure():

    # Simulate Yahoo Finance becoming unavailable.
    with patch(
        "app.api.main.fetch_option_chain",
        side_effect=RuntimeError("Provider unavailable")
    ):

        response = client.get(
            "/api/v1/market/options/SPY"
        )

    assert response.status_code == 503

    assert response.json()["detail"] == (
        "Market data is temporarily unavailable."
    )