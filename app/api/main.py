"""
Quant Options Engine REST API.

Provides endpoints for:
- Health checks.
- European option pricing.
- Analytical option Greeks.
- Implied volatility.
- Yahoo Finance option-chain data.
- Vectorized batch option pricing.
- Vectorized batch option Greeks.
- Portfolio theoretical valuation.
- Portfolio aggregate Greeks.
- Portfolio scenario analysis.

All pricing and risk calculations reuse the project's
existing quantitative analytics modules.
"""

import logging
import math

import numpy as np
from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator
from starlette.concurrency import run_in_threadpool

from app.market_data.yahoo_client import fetch_option_chain
from app.pricing.black_scholes import BlackScholes
from app.pricing.implied_volatility import implied_volatility
from app.pricing.portfolio import OptionPosition, PortfolioAnalytics
from app.pricing.scenario_analysis import (
    MarketScenario,
    PortfolioScenarioAnalysis,
)
from app.pricing.vectorized_black_scholes import (
    greeks_options_vectorized,
    price_options_vectorized,
)

# ============================================================
# LOGGING CONFIGURATION
# ============================================================

# Create a dedicated logger for this module.
#
# __name__ identifies the module as "app.api.main".
# This allows logs to be organized by module.
logger = logging.getLogger(__name__)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

# Version 1.3.0 adds portfolio analytics and scenario endpoints.
app = FastAPI(
    title="Quant Options Engine",
    description="Options pricing and quantitative analytics REST API.",
    version="1.3.0",
)


# ============================================================
# SAFE REQUEST VALIDATION ERROR HANDLER
# ============================================================

def make_validation_error_json_safe(value):
    """
    Recursively convert validation-error details into JSON-safe values.

    FastAPI includes the rejected input in validation errors.

    When that input is NaN, Infinity, or -Infinity, the default
    JSON response serializer can raise ValueError because those
    floating-point values are not permitted in standard JSON.

    Convert non-finite floats into descriptive strings while
    preserving the original validation error information.
    """

    if isinstance(value, float):

        if math.isnan(value):
            return "NaN"

        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"

        return value

    if isinstance(value, dict):
        return {
            str(key): make_validation_error_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            make_validation_error_json_safe(item)
            for item in value
        ]

    return value


@app.exception_handler(RequestValidationError)
async def safe_request_validation_error_handler(
    request: Request,
    exc: RequestValidationError,
):
    """
    Return HTTP 422 for invalid requests without JSON serialization errors.

    The handler preserves FastAPI's normal validation-error structure:

        {"detail": [...]}

    Non-finite numbers in error details are represented as strings.
    """

    safe_errors = make_validation_error_json_safe(
        exc.errors()
    )

    return JSONResponse(
        status_code=422,
        content=jsonable_encoder(
            {"detail": safe_errors}
        ),
    )


# ============================================================
# REQUEST MODEL 1: INDIVIDUAL OPTION
# ============================================================

class OptionRequest(BaseModel):
    """
    Validate inputs for individual European option calculations.
    """

    # Reject unexpected request fields.
    model_config = ConfigDict(extra="forbid")

    # Current underlying asset price.
    S: float = Field(gt=0, allow_inf_nan=False)

    # Option strike price.
    K: float = Field(gt=0, allow_inf_nan=False)

    # Time remaining until expiration, in years.
    T: float = Field(ge=0, allow_inf_nan=False)

    # Annual continuously compounded risk-free rate.
    r: float = Field(allow_inf_nan=False)

    # Annualized volatility as a decimal.
    sigma: float = Field(ge=0, allow_inf_nan=False)

    # Continuous dividend yield.
    q: float = Field(default=0.0, allow_inf_nan=False)


# ============================================================
# REQUEST MODEL 2: BATCH OPTIONS
# ============================================================

class BatchOptionRequest(BaseModel):
    """
    Validate a batch of European option contracts.

    Shared by:
    - /api/v1/options/batch-price
    - /api/v1/options/batch-greeks
    """

    model_config = ConfigDict(extra="forbid")

    # Restrict batch size to between 1 and 10,000 options.
    options: list[OptionRequest] = Field(
        min_length=1,
        max_length=10_000,
    )


# ============================================================
# REQUEST MODEL 3: IMPLIED VOLATILITY
# ============================================================

class ImpliedVolatilityRequest(BaseModel):
    """
    Validate inputs for the implied-volatility solver.
    """

    model_config = ConfigDict(extra="forbid")

    # Observed market price of the option.
    market_price: float = Field(ge=0, allow_inf_nan=False)

    # Underlying asset price.
    S: float = Field(gt=0, allow_inf_nan=False)

    # Strike price.
    K: float = Field(gt=0, allow_inf_nan=False)

    # Time to expiration must be strictly positive.
    T: float = Field(gt=0, allow_inf_nan=False)

    # Annual risk-free rate.
    r: float = Field(allow_inf_nan=False)

    # Supported option types.
    option_type: str = Field(
        default="call",
        pattern="^(call|put)$",
    )

    # Continuous dividend yield.
    q: float = Field(default=0.0, allow_inf_nan=False)


# ============================================================
# REQUEST MODEL 4: PORTFOLIO OPTION POSITION
# ============================================================

class PortfolioPositionRequest(BaseModel):
    """
    Validate one option position submitted to the portfolio API.

    quantity:
        Positive = long contracts.
        Negative = short contracts.

    multiplier:
        Number of underlying units represented by one contract.

    Each position contains its own strike, expiration,
    volatility, interest rate, and dividend yield.
    """

    model_config = ConfigDict(extra="forbid")

    # European call or put.
    option_type: str = Field(pattern="^(call|put)$")

    # Signed number of contracts.
    #
    # strict=True prevents floats such as 10.5
    # from being converted into integers.
    quantity: int = Field(strict=True)

    # Current underlying price.
    S: float = Field(gt=0, allow_inf_nan=False)

    # Strike price.
    K: float = Field(gt=0, allow_inf_nan=False)

    # Time to expiration in years.
    T: float = Field(ge=0, allow_inf_nan=False)

    # Annual risk-free rate.
    r: float = Field(allow_inf_nan=False)

    # Annualized volatility.
    sigma: float = Field(ge=0, allow_inf_nan=False)

    # Continuous dividend yield.
    q: float = Field(default=0.0, allow_inf_nan=False)

    # Standard equity options typically use 100.
    multiplier: int = Field(
        default=100,
        gt=0,
        strict=True,
    )

    # ========================================================
    # VALIDATE NONZERO QUANTITY
    # ========================================================

    @model_validator(mode="after")
    def validate_quantity(self):
        """
        Reject positions containing zero contracts.
        """

        if self.quantity == 0:
            raise ValueError(
                "quantity cannot be zero."
            )

        return self


# ============================================================
# REQUEST MODEL 5: PORTFOLIO
# ============================================================

class PortfolioRequest(BaseModel):
    """
    Validate a portfolio containing European option positions.

    This version supports a single underlying asset.

    Therefore, all positions must share the same
    current underlying price S.
    """

    model_config = ConfigDict(extra="forbid")

    # Require between 1 and 10,000 positions.
    positions: list[PortfolioPositionRequest] = Field(
        min_length=1,
        max_length=10_000,
    )

    # ========================================================
    # VALIDATE COMMON UNDERLYING PRICE
    # ========================================================

    @model_validator(mode="after")
    def validate_underlying_prices(self):
        """
        Ensure every position uses the same underlying price.
        """

        first_price = self.positions[0].S

        for position in self.positions[1:]:

            if position.S != first_price:
                raise ValueError(
                    "All positions must use the same "
                    "underlying price S."
                )

        return self


# ============================================================
# REQUEST MODEL 6: MARKET SCENARIO
# ============================================================

class MarketScenarioRequest(BaseModel):
    """
    Validate one hypothetical market scenario.

    price_change_pct:
        Percentage change in the underlying price.

        Example:
            -5.0 means the stock decreases by 5%.

    volatility_change:
        Absolute change in annualized volatility.

        Example:
            +0.05 means volatility increases
            by 5 percentage points.

    days_forward:
        Number of calendar days to advance.
    """

    model_config = ConfigDict(extra="forbid")

    # Descriptive scenario name.
    name: str = Field(min_length=1)

    # Percentage stock-price change.
    #
    # Greater than -100 prevents a zero or
    # negative underlying price.
    price_change_pct: float = Field(
        default=0.0,
        gt=-100,
        allow_inf_nan=False,
    )

    # Absolute change in annualized volatility.
    volatility_change: float = Field(
        default=0.0,
        allow_inf_nan=False,
    )

    # Nonnegative calendar-day advancement.
    days_forward: float = Field(
        default=0.0,
        ge=0,
        allow_inf_nan=False,
    )

    # ========================================================
    # VALIDATE NONEMPTY SCENARIO NAME
    # ========================================================

    @model_validator(mode="after")
    def validate_name(self):
        """
        Reject names containing only whitespace.
        """

        if not self.name.strip():
            raise ValueError(
                "Scenario name cannot be blank."
            )

        return self


# ============================================================
# REQUEST MODEL 7: PORTFOLIO SCENARIO ANALYSIS
# ============================================================

class PortfolioScenarioRequest(PortfolioRequest):
    """
    Validate a portfolio and its hypothetical market scenarios.

    Inherits the portfolio position validation from
    PortfolioRequest and adds the scenario collection.
    """

    # Require between 1 and 100 scenarios.
    #
    # With the maximum 10,000 positions, this allows
    # up to 1,000,000 scenario-position combinations.
    scenarios: list[MarketScenarioRequest] = Field(
        min_length=1,
        max_length=100,
    )

    # ========================================================
    # VALIDATE UNIQUE SCENARIO NAMES
    # ========================================================

    @model_validator(mode="after")
    def validate_unique_scenario_names(self):
        """
        Reject duplicate scenario names.
        """

        names = [
            scenario.name
            for scenario in self.scenarios
        ]

        if len(names) != len(set(names)):
            raise ValueError(
                "Scenario names must be unique."
            )

        return self


# ============================================================
# HELPER: BUILD PORTFOLIO ENGINE
# ============================================================

def build_portfolio_engine(
    positions: list[PortfolioPositionRequest],
):
    """
    Convert validated API position models into OptionPosition objects.

    This helper is shared by all portfolio endpoints.

    It prevents duplication of position conversion logic.
    """

    # Convert each Pydantic model into a validated
    # OptionPosition dataclass.
    portfolio_positions = [
        OptionPosition(
            option_type=position.option_type,
            quantity=position.quantity,
            S=position.S,
            K=position.K,
            T=position.T,
            r=position.r,
            sigma=position.sigma,
            q=position.q,
            multiplier=position.multiplier,
        )
        for position in positions
    ]

    # Return the existing portfolio analytics engine.
    return PortfolioAnalytics(portfolio_positions)


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
    call_prices, put_prices = price_options_vectorized(
        S=stock_prices,
        K=strikes,
        T=expirations,
        r=interest_rates,
        sigma=volatilities,
        q=dividend_yields,
    )

    # Convert NumPy results into JSON-compatible floats.
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

    Undefined Greeks are returned as JSON null.
    """

    # ========================================================
    # CONVERT VALIDATED INPUTS INTO NUMPY ARRAYS
    # ========================================================

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

    # ========================================================
    # CALCULATE VECTORIZED PRICES AND GREEKS
    # ========================================================

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

    for index in range(len(request.options)):

        contract_result = {}

        for field in output_fields:

            value = float(vectorized_results[field][index])

            # Convert undefined Greeks into JSON null.
            if math.isnan(value):

                contract_result[field] = None

            else:

                # Match the scalar engine's rounding convention.
                contract_result[field] = round(value, 4)

        results.append(contract_result)

    return {
        "count": len(results),
        "results": results,
    }


# ============================================================
# ENDPOINT 8: PORTFOLIO THEORETICAL VALUATION
# ============================================================

@app.post("/api/v1/portfolio/value")
def calculate_portfolio_value(request: PortfolioRequest):
    """
    Calculate theoretical portfolio value and position breakdown.

    Accepts between 1 and 10,000 European option positions.

    Returns:
    - Number of positions.
    - Gross and net contract counts.
    - Total theoretical portfolio value.
    - Individual position values.

    Notes
    -----
    This endpoint intentionally returns valuation information
    without exposing aggregate portfolio Greeks.

    For the complete risk report, use:
    POST /api/v1/portfolio/greeks
    """

    # ========================================================
    # BUILD PORTFOLIO
    # ========================================================

    portfolio = build_portfolio_engine(request.positions)

    # ========================================================
    # CALCULATE PORTFOLIO ANALYTICS
    # ========================================================

    # The existing engine calculates prices and Greeks
    # together in one vectorized operation.
    report = portfolio.calculate()

    # ========================================================
    # BUILD VALUATION-ONLY POSITION RESULTS
    # ========================================================

    # Return pricing fields without individual Greeks.
    positions = [
        {
            "position_index": position["position_index"],
            "option_type": position["option_type"],
            "quantity": position["quantity"],
            "multiplier": position["multiplier"],
            "S": position["S"],
            "K": position["K"],
            "T": position["T"],
            "r": position["r"],
            "sigma": position["sigma"],
            "q": position["q"],
            "option_price": position["option_price"],
            "position_value": position["position_value"],
        }
        for position in report["positions"]
    ]

    # ========================================================
    # RETURN VALUATION REPORT
    # ========================================================

    return {
        "position_count": report["position_count"],
        "total_contracts": report["total_contracts"],
        "net_contracts": report["net_contracts"],
        "portfolio_value": report["portfolio_value"],
        "positions": positions,
    }


# ============================================================
# ENDPOINT 9: PORTFOLIO AGGREGATE GREEKS
# ============================================================

@app.post("/api/v1/portfolio/greeks")
def calculate_portfolio_greeks(request: PortfolioRequest):
    """
    Calculate portfolio theoretical value and aggregate Greeks.

    Returns the complete report produced by PortfolioAnalytics.

    Includes:
    - Portfolio value.
    - Aggregate delta.
    - Aggregate gamma.
    - Aggregate vega.
    - Aggregate theta.
    - Aggregate rho.
    - Position-level Greek contributions.

    Undefined Greeks are returned as JSON null.
    """

    # Build the validated portfolio engine.
    portfolio = build_portfolio_engine(request.positions)

    # Reuse the existing vectorized portfolio implementation.
    #
    # This avoids duplicating Greeks formulas inside the API.
    return portfolio.calculate()


# ============================================================
# ENDPOINT 10: PORTFOLIO SCENARIO ANALYSIS
# ============================================================

@app.post("/api/v1/portfolio/scenarios")
def calculate_portfolio_scenarios(
    request: PortfolioScenarioRequest,
):
    """
    Reprice an options portfolio under hypothetical scenarios.

    Each scenario can modify:
    - Underlying price.
    - Annualized volatility.
    - Time remaining until expiration.

    Returns:
    - Original theoretical portfolio value.
    - Scenario theoretical portfolio values.
    - Scenario theoretical P&L.
    - Normalized scenario value changes.
    - Position-level scenario P&L.

    Scenario results are not forecasts or realized trading P&L.
    """

    # ========================================================
    # BUILD PORTFOLIO
    # ========================================================

    portfolio = build_portfolio_engine(request.positions)

    # ========================================================
    # CONVERT API SCENARIOS INTO DOMAIN MODELS
    # ========================================================

    scenarios = [
        MarketScenario(
            name=scenario.name,
            price_change_pct=scenario.price_change_pct,
            volatility_change=scenario.volatility_change,
            days_forward=scenario.days_forward,
        )
        for scenario in request.scenarios
    ]

    # ========================================================
    # CREATE SCENARIO ANALYSIS ENGINE
    # ========================================================

    analysis = PortfolioScenarioAnalysis(
        portfolio=portfolio,
        scenarios=scenarios,
    )

    # ========================================================
    # CALCULATE SCENARIO REPORT
    # ========================================================

    try:

        # The scenario engine checks whether the shocks
        # produce valid market parameters.
        #
        # For example, a -0.30 volatility shock is invalid
        # for a position with starting volatility 0.20.
        return analysis.calculate()

    except ValueError as exc:

        # Convert domain validation errors into HTTP 422.
        #
        # Without this conversion, an invalid volatility
        # scenario would produce an internal server error.
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc