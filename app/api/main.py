import math

from fastapi import FastAPI
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.pricing.black_scholes import BlackScholes
from app.pricing.implied_volatility import implied_volatility

from fastapi import HTTPException
from starlette.concurrency import run_in_threadpool

from app.market_data.yahoo_client import fetch_option_chain



# Create the FastAPI application.
app = FastAPI(
    title="Quant Options Engine",
    description="Options pricing and quantitative analytics REST API.",
    version="1.0.0"
)


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


# Endpoint 1: Health check.
@app.get("/health")
def health_check():

    return {
        "status": "healthy",
        "service": "quant-options-engine"
    }


# Endpoint 2: Calculate option prices.
@app.post("/api/v1/options/price")
def calculate_option_price(request: OptionRequest):

    engine = BlackScholes(
        S=request.S,
        K=request.K,
        T=request.T,
        r=request.r,
        sigma=request.sigma,
        q=request.q
    )

    return {
        "call_price": round(engine.call_price(), 4),
        "put_price": round(engine.put_price(), 4)
    }


# Endpoint 3: Calculate option Greeks.
@app.post("/api/v1/options/greeks")
def calculate_option_greeks(request: OptionRequest):

    engine = BlackScholes(
        S=request.S,
        K=request.K,
        T=request.T,
        r=request.r,
        sigma=request.sigma,
        q=request.q
    )

    return engine.greeks()


# Endpoint 4: Calculate implied volatility from a market option price.
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
        q=request.q
    )

    # Some market prices have no valid implied volatility
    # within the solver's configured range.
    if not math.isfinite(iv):

        raise HTTPException(
            status_code=422,
            detail="No valid implied volatility found for these inputs."
        )

    return {
        "implied_volatility": round(iv, 6),
        "implied_volatility_percent": round(iv * 100, 4)
    }


    # Endpoint 5: Retrieve market option quotes and calculated IVs.
@app.get("/api/v1/market/options/{ticker}")
async def get_market_options(
    ticker: str,
    risk_free_rate: float = 0.045,
    dividend_yield: float = 0.0,
    minimum_days_to_expiry: int = 7
):

    # Restrict ticker symbols to common alphanumeric formats.
    # This prevents unexpected characters from being passed
    # directly into our market-data provider.
    import re

    ticker = ticker.upper()

    if not re.fullmatch(r"[A-Z0-9.^-]{1,15}", ticker):
        raise HTTPException(
            status_code=422,
            detail="Invalid ticker symbol."
        )

    # Validate query parameters.
    if not all(
        math.isfinite(value)
        for value in (risk_free_rate, dividend_yield)
    ):
        raise HTTPException(
            status_code=422,
            detail="Interest rate and dividend yield must be finite."
        )

    if minimum_days_to_expiry < 1 or minimum_days_to_expiry > 365:
        raise HTTPException(
            status_code=422,
            detail="minimum_days_to_expiry must be between 1 and 365."
        )

    try:

        # Yahoo Finance requests are synchronous and can be slow.
        # Running them in a thread prevents blocking the API event loop.
        df = await run_in_threadpool(
            fetch_option_chain,
            ticker_symbol=ticker,
            risk_free_rate=risk_free_rate,
            dividend_yield=dividend_yield,
            minimum_days_to_expiry=minimum_days_to_expiry
        )

    except Exception as exc:

        # Log the actual error for debugging.
        import logging
        logging.exception("Market data request failed")

        # Avoid exposing internal provider errors to API users.
        raise HTTPException(
            status_code=503,
            detail="Market data is temporarily unavailable."
        ) from exc

    # Convert the DataFrame into JSON-compatible records.
    records = df.to_dict(orient="records")

    return {
        "ticker": ticker,
        "count": len(records),
        "options": records
    }