import logging
import math

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from starlette.concurrency import run_in_threadpool

from app.market_data.yahoo_client import fetch_option_chain
from app.pricing.black_scholes import BlackScholes
from app.pricing.implied_volatility import implied_volatility
from app.pricing.vectorized_black_scholes import (
    greeks_options_vectorized,
    price_options_vectorized,
)

# ============================================================
# LOGGING CONFIGURATION
# ============================================================

# Create a dedicated logger for this Python module.
#
# __name__ identifies the module as "app.api.main".
# This allows application logs to be organized by module
# instead of using Python's global/root logger.
#
# When an unexpected error occurs, this logger can record
# the error message and traceback for debugging.
logger = logging.getLogger(__name__)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

# Create the FastAPI application.
app = FastAPI(
    title="Quant Options Engine",
    description="Options pricing and quantitative analytics REST API.",
    version="1.2.0",
)


# ============================================================
# REQUEST MODELS
# ============================================================

# Define the structure of an incoming option-pricing request.
class OptionRequest(BaseModel):

    # Reject unexpected request fields.
    model_config = ConfigDict(extra="forbid")

    # Current stock price.
    S: float = Field(gt=0, allow_inf_nan=False)

    # Option strike price.
    K: float = Field(gt=0, allow_inf_nan=False)

    # Time remaining until expiration, measured in years.
    T: float = Field(ge=0, allow_inf_nan=False)

    # Continuously compounded annual risk-free rate.
    r: float = Field(allow_inf_nan=False)

    # Annualized volatility as a decimal.
    sigma: float = Field(ge=0, allow_inf_nan=False)

    # Continuously compounded annual dividend yield.
    q: float = Field(default=0.0, allow_inf_nan=False)


# Define the structure of a batch-pricing request.
#
# This model is shared by both batch endpoints:
#
# POST /api/v1/options/batch-price
# POST /api/v1/options/batch-greeks
#
# Sharing the model guarantees consistent validation.
class BatchOptionRequest(BaseModel):

    # Reject unexpected fields at the outer request level.
    model_config = ConfigDict(extra="forbid")

    # Accept between 1 and 10,000 option contracts.
    #
    # Each contract uses OptionRequest, so every item
    # receives the same validation as the single-option API.
    options: list[OptionRequest] = Field(
        min_length=1,
        max_length=10_000,
    )


# Define the inputs required to calculate implied volatility.
class ImpliedVolatilityRequest(BaseModel):

    # Reject unexpected JSON fields.
    model_config = ConfigDict(extra="forbid")

    # Observed option market price.
    market_price: float = Field(ge=0, allow_inf_nan=False)

    # Current underlying stock price.
    S: float = Field(gt=0, allow_inf_nan=False)

    # Option strike price.
    K: float = Field(gt=0, allow_inf_nan=False)

    # Time remaining until expiration in years.
    T: float = Field(gt=0, allow_inf_nan=False)

    # Annual risk-free interest rate.
    r: float = Field(allow_inf_nan=False)

    # Option type: call or put.
    option_type: str = Field(default="call", pattern="^(call|put)$")

    # Annual dividend yield.
    q: float = Field(default=0.0, allow_inf_nan=False)


# ============================================================
# ENDPOINT 1: HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "service": "quant-options-engine",
    }


# ============================================================
# ENDPOINT 2: OPTION PRICING
# ============================================================

@app.post("/api/v1/options/price")
def calculate_option_price(request: OptionRequest):

    # Initialize the Black-Scholes pricing engine
    # using the values supplied in the API request.
    engine = BlackScholes(
        S=request.S,
        K=request.K,
        T=request.T,
        r=request.r,
        sigma=request.sigma,
        q=request.q,
    )

    # Return the theoretical European call and put prices.
    return {
        "call_price": round(engine.call_price(), 4),
        "put_price": round(engine.put_price(), 4),
    }


# ============================================================
# ENDPOINT 3: OPTION GREEKS
# ============================================================

@app.post("/api/v1/options/greeks")
def calculate_option_greeks(request: OptionRequest):

    # Initialize the pricing engine using the request inputs.
    engine = BlackScholes(
        S=request.S,
        K=request.K,
        T=request.T,
        r=request.r,
        sigma=request.sigma,
        q=request.q,
    )

    # Return the option sensitivity measurements.
    return engine.greeks()


# ============================================================
# ENDPOINT 4: IMPLIED VOLATILITY
# ============================================================

@app.post("/api/v1/options/implied-volatility")
def calculate_implied_volatility(request: ImpliedVolatilityRequest):

    # Use Brent's method to solve for implied volatility.
    iv = implied_volatility(
        market_price=request.market_price,
        S=request.S,
        K=request.K,
        T=request.T,
        r=request.r,
        option_type=request.option_type,
        q=request.q,
    )

    # Some market prices have no valid implied volatility
    # within the solver's configured range.
    if not math.isfinite(iv):

        raise HTTPException(
            status_code=422,
            detail="No valid implied volatility found for these inputs.",
        )

    # Return implied volatility as both a decimal and percentage.
    return {
        "implied_volatility": round(iv, 6),
        "implied_volatility_percent": round(iv * 100, 4),
    }


# ============================================================
# ENDPOINT 5: YAHOO FINANCE MARKET DATA
# ============================================================

@app.get("/api/v1/market/options/{ticker}")
async def get_market_options(
    ticker: str,
    risk_free_rate: float = 0.045,
    dividend_yield: float = 0.0,
    minimum_days_to_expiry: int = 7,
):

    # Restrict ticker symbols to common alphanumeric formats.
    # This prevents unexpected characters from being passed
    # directly into our market-data provider.
    import re

    ticker = ticker.upper()

    if not re.fullmatch(r"[A-Z0-9.^-]{1,15}", ticker):
        raise HTTPException(
            status_code=422,
            detail="Invalid ticker symbol.",
        )

    # Validate query parameters.
    if not all(
        math.isfinite(value)
        for value in (risk_free_rate, dividend_yield)
    ):
        raise HTTPException(
            status_code=422,
            detail="Interest rate and dividend yield must be finite.",
        )

    if minimum_days_to_expiry < 1 or minimum_days_to_expiry > 365:
        raise HTTPException(
            status_code=422,
            detail="minimum_days_to_expiry must be between 1 and 365.",
        )

    try:

        # Yahoo Finance requests are synchronous and can be slow.
        # Running them in a thread prevents blocking the API event loop.
        df = await run_in_threadpool(
            fetch_option_chain,
            ticker_symbol=ticker,
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
            minimum_days_to_expiry=minimum_days_to_expiry,
        )

    except Exception as exc:

        # Record the unexpected error using our dedicated logger.
        #
        # logger.exception() automatically includes the
        # exception traceback when called inside an except block.
        #
        # This helps developers diagnose failures without
        # exposing internal provider errors to API users.
        logger.exception("Market data request failed")

        # Return a generic HTTP 503 response to the API client.
        #
        # HTTP 503 means the service is temporarily unavailable.
        # The original exception is preserved internally.
        raise HTTPException(
            status_code=503,
            detail="Market data is temporarily unavailable.",
        ) from exc

    # Convert the DataFrame into JSON-compatible records.
    records = df.to_dict(orient="records")

    return {
        "ticker": ticker,
        "count": len(records),
        "options": records,
    }


# ============================================================
# ENDPOINT 6: VECTORIZED BATCH OPTION PRICING
# ============================================================

@app.post("/api/v1/options/batch-price")
def calculate_batch_option_prices(request: BatchOptionRequest):

    # Convert the validated option contracts into NumPy arrays.
    #
    # Each array contains one parameter for every contract.
    # For example, strikes might contain:
    #
    # [90.0, 100.0, 110.0]
    #
    # NumPy arrays allow the pricing engine to process
    # the entire batch instead of using a Python loop
    # to price every contract individually.

    stock_prices = np.array(
        [option.S for option in request.options],
        dtype=float,
    )

    strikes = np.array(
        [option.K for option in request.options],
        dtype=float,
    )

    expirations = np.array(
        [option.T for option in request.options],
        dtype=float,
    )

    interest_rates = np.array(
        [option.r for option in request.options],
        dtype=float,
    )

    volatilities = np.array(
        [option.sigma for option in request.options],
        dtype=float,
    )

    dividend_yields = np.array(
        [option.q for option in request.options],
        dtype=float,
    )

    # Calculate every call and put price in one vectorized operation.
    #
    # Both arrays preserve the order of the incoming contracts.
    call_prices, put_prices = price_options_vectorized(
        S=stock_prices,
        K=strikes,
        T=expirations,
        r=interest_rates,
        sigma=volatilities,
        q=dividend_yields,
    )

    # Build the JSON-compatible response.
    #
    # zip() pairs the call and put price for each contract.
    #
    # float() converts NumPy numbers into standard Python floats.
    # round() keeps the response consistent with the existing
    # single-option pricing endpoint.
    results = [
        {
            "call_price": round(float(call), 4),
            "put_price": round(float(put), 4),
        }
        for call, put in zip(
            call_prices,
            put_prices,
            strict=True,
        )
    ]

    # Return the number of priced contracts and their prices.
    return {
        "count": len(results),
        "results": results,
    }


# ============================================================
# ENDPOINT 7: VECTORIZED BATCH OPTION GREEKS
# ============================================================

@app.post("/api/v1/options/batch-greeks")
def calculate_batch_option_greeks(request: BatchOptionRequest):
    """
    Calculate European option prices and Greeks for a batch.

    Accepts between 1 and 10,000 option contracts.

    Each result contains:
    - Call price
    - Put price
    - Call delta
    - Put delta
    - Gamma
    - Vega
    - Call theta
    - Put theta
    - Call rho
    - Put rho

    Undefined Greeks are returned as JSON null.
    """

    # ========================================================
    # CONVERT VALIDATED INPUTS INTO NUMPY ARRAYS
    # ========================================================

    # Extract stock prices from all submitted contracts.
    stock_prices = np.array(
        [option.S for option in request.options],
        dtype=float,
    )

    # Extract strike prices.
    strikes = np.array(
        [option.K for option in request.options],
        dtype=float,
    )

    # Extract time to expiration, measured in years.
    expirations = np.array(
        [option.T for option in request.options],
        dtype=float,
    )

    # Extract continuously compounded risk-free rates.
    interest_rates = np.array(
        [option.r for option in request.options],
        dtype=float,
    )

    # Extract annualized volatility values.
    volatilities = np.array(
        [option.sigma for option in request.options],
        dtype=float,
    )

    # Extract continuously compounded dividend yields.
    dividend_yields = np.array(
        [option.q for option in request.options],
        dtype=float,
    )

    # ========================================================
    # CALCULATE VECTORIZED PRICES AND GREEKS
    # ========================================================

    # Process the entire batch in one NumPy operation.
    #
    # The function returns a dictionary containing ten
    # NumPy arrays, one for each output field.
    #
    # Each array has one entry per option contract.
    vectorized_results = greeks_options_vectorized(
        S=stock_prices,
        K=strikes,
        T=expirations,
        r=interest_rates,
        sigma=volatilities,
        q=dividend_yields,
    )

    # ========================================================
    # DEFINE OUTPUT FIELD ORDER
    # ========================================================

    # Keep the response fields consistent with the original
    # BlackScholes.greeks() method.
    output_fields = (
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

    # ========================================================
    # BUILD JSON-COMPATIBLE RESULTS
    # ========================================================

    results = []

    # Iterate over the original contract positions.
    #
    # Although the mathematical calculations are vectorized,
    # a Python loop is still needed to build individual JSON
    # objects for the API response.
    #
    # This does not change the fact that the pricing and
    # Greeks calculations themselves are vectorized.
    for index in range(len(request.options)):

        contract_result = {}

        # Extract each of the ten calculated outputs.
        for field in output_fields:

            value = float(vectorized_results[field][index])

            # Undefined analytical Greeks are represented
            # internally using NumPy NaN values.
            #
            # JSON does not support NaN as a standard value.
            #
            # Convert NaN into Python None, which FastAPI
            # serializes as JSON null.
            if math.isnan(value):

                contract_result[field] = None

            else:

                # Match the scalar Black-Scholes engine's
                # four-decimal rounding convention.
                contract_result[field] = round(value, 4)

        results.append(contract_result)

    # ========================================================
    # RETURN BATCH RESPONSE
    # ========================================================

    return {
        "count": len(results),
        "results": results,
    }