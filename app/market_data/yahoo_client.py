import math
from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

from app.pricing.implied_volatility import implied_volatility

# US equity options use the New York market timezone.
MARKET_TIMEZONE = ZoneInfo("America/New_York")


# ============================================================
# OPTION QUOTE VALIDATION
# ============================================================

def is_valid_option_quote(
    strike: float,
    bid: float,
    ask: float,
    maximum_relative_spread: float = 0.30
) -> bool:
    """
    Validate an option's strike, bid, and ask prices.

    Rejects:
    - Missing or non-numeric values.
    - Non-finite values.
    - Nonpositive strikes, bids, or asks.
    - Crossed markets where bid exceeds ask.
    - Quotes exceeding the maximum relative spread.

    Relative spread = (ask - bid) / midpoint
    """

    try:
        strike = float(strike)
        bid = float(bid)
        ask = float(ask)
        maximum_relative_spread = float(maximum_relative_spread)

    except (TypeError, ValueError, OverflowError):
        return False

    if not all(
        math.isfinite(value)
        for value in (
            strike,
            bid,
            ask,
            maximum_relative_spread
        )
    ):
        return False

    if strike <= 0 or bid <= 0 or ask <= 0:
        return False

    if bid > ask:
        return False

    if maximum_relative_spread < 0:
        return False

    midpoint = (bid + ask) / 2.0

    relative_spread = (ask - bid) / midpoint

    if relative_spread > maximum_relative_spread:
        return False

    return True


# ============================================================
# TIME TO EXPIRATION
# ============================================================

def calculate_time_to_expiration(expiration_date: str) -> float:
    """
    Calculate time remaining until expiration.

    Assumes expiration occurs at 4:00 PM New York time
    on the supplied expiration date.

    Returns remaining time in calendar years.
    """

    expiration = datetime.strptime(
        expiration_date,
        "%Y-%m-%d"
    ).date()

    expiration_datetime = datetime.combine(
        expiration,
        time(16, 0),
        tzinfo=MARKET_TIMEZONE
    )

    current_datetime = datetime.now(MARKET_TIMEZONE)

    remaining_seconds = (
        expiration_datetime.timestamp()
        - current_datetime.timestamp()
    )

    seconds_per_year = 365.0 * 24.0 * 60.0 * 60.0

    return max(remaining_seconds / seconds_per_year, 0.0)


# ============================================================
# TIMESTAMP HELPERS
# ============================================================

def normalize_timestamp(value):
    """
    Convert a timestamp into a UTC ISO 8601 string.

    Returns None when the timestamp is missing or invalid.

    Naive timestamps are deliberately rejected because
    their timezone cannot be determined reliably.
    """

    if value is None:
        return None

    try:
        timestamp = pd.Timestamp(value)

        if pd.isna(timestamp):
            return None

        if timestamp.tzinfo is None:
            return None

        return timestamp.tz_convert(
            "UTC"
        ).isoformat()

    except (TypeError, ValueError, OverflowError):
        return None


def calculate_observation_age_hours(
    observation_timestamp,
    reference_timestamp
):
    """
    Calculate the age of an observation in hours.

    Both timestamps must contain timezone information.

    Returns None when either timestamp is invalid or
    when the observation is later than the reference time.
    """

    observation = normalize_timestamp(
        observation_timestamp
    )

    reference = normalize_timestamp(
        reference_timestamp
    )

    if observation is None or reference is None:
        return None

    observation_dt = pd.Timestamp(observation)
    reference_dt = pd.Timestamp(reference)

    age_hours = (
        reference_dt - observation_dt
    ).total_seconds() / 3600.0

    if age_hours < 0:
        return None

    return round(age_hours, 4)


# ============================================================
# YAHOO FINANCE OPTION CHAIN
# ============================================================

def fetch_option_chain(
    ticker_symbol: str = "SPY",
    risk_free_rate: float = 0.045,
    dividend_yield: float = 0.0,
    minimum_days_to_expiry: int = 7,
    maximum_relative_spread: float = 0.30
) -> pd.DataFrame:
    """
    Download call-option quotes and calculate implied volatility.

    Also records:
    - Data retrieval timestamp.
    - Underlying price observation timestamp.
    - Underlying observation age.
    - Option last-trade timestamp.
    - Option last-trade age.

    Important:
    An option's last-trade timestamp is NOT its bid/ask
    quote timestamp. It must not be interpreted as proof
    that the quote is fresh.
    """

    # --------------------------------------------------------
    # STEP 1: RECORD DATA RETRIEVAL TIME
    # --------------------------------------------------------

    # Record when the market-data request begins.
    retrieval_timestamp = datetime.now(UTC)

    retrieval_time_iso = retrieval_timestamp.isoformat()

    print(f"Fetching market data for {ticker_symbol}...")

    # --------------------------------------------------------
    # STEP 2: RETRIEVE UNDERLYING PRICE
    # --------------------------------------------------------

    ticker = yf.Ticker(ticker_symbol)

    history = ticker.history(period="5d")

    if history.empty:
        raise RuntimeError(
            "No underlying price data available."
        )

    stock_price = float(
        history["Close"].iloc[-1]
    )

    if not math.isfinite(stock_price) or stock_price <= 0:
        raise RuntimeError(
            "Invalid underlying price received."
        )

    # The final row's index identifies the daily price bar.
    # It is not necessarily the exact time of the last trade.
    underlying_timestamp = normalize_timestamp(
        history.index[-1]
    )

    underlying_age_hours = calculate_observation_age_hours(
        underlying_timestamp,
        retrieval_timestamp
    )

    print(
        f"Latest {ticker_symbol} price: "
        f"${stock_price:.2f}"
    )

    # --------------------------------------------------------
    # STEP 3: SELECT EXPIRATION
    # --------------------------------------------------------

    expirations = ticker.options

    if not expirations:
        raise RuntimeError(
            "No options expirations available."
        )

    today = datetime.now(MARKET_TIMEZONE).date()

    minimum_expiration = today + timedelta(
        days=minimum_days_to_expiry
    )

    eligible_expirations = [
        expiration
        for expiration in expirations
        if datetime.strptime(
            expiration,
            "%Y-%m-%d"
        ).date() >= minimum_expiration
    ]

    if not eligible_expirations:
        raise RuntimeError(
            "No suitable expiration dates available."
        )

    expiration_date = eligible_expirations[0]

    T = calculate_time_to_expiration(
        expiration_date
    )

    if T <= 0:
        raise RuntimeError(
            "Selected options have already expired."
        )

    print(
        f"Selected expiration: {expiration_date}"
    )

    print(
        f"Time to expiration: {T:.6f} years"
    )

    # --------------------------------------------------------
    # STEP 4: DOWNLOAD OPTION CHAIN
    # --------------------------------------------------------

    option_chain = ticker.option_chain(
        expiration_date
    )

    calls = option_chain.calls.copy()

    results = []

    # --------------------------------------------------------
    # STEP 5: PROCESS OPTION QUOTES
    # --------------------------------------------------------

    for _, row in calls.iterrows():

        strike = row["strike"]
        bid = row["bid"]
        ask = row["ask"]

        # Reject unusable or excessively wide quotes.
        if not is_valid_option_quote(
            strike=strike,
            bid=bid,
            ask=ask,
            maximum_relative_spread=maximum_relative_spread
        ):
            continue

        strike = float(strike)
        bid = float(bid)
        ask = float(ask)

        market_price = (bid + ask) / 2.0

        # Calculate implied volatility.
        iv = implied_volatility(
            market_price=market_price,
            S=stock_price,
            K=strike,
            T=T,
            r=risk_free_rate,
            option_type="call",
            q=dividend_yield
        )

        if not math.isfinite(iv):
            continue

        # ----------------------------------------------------
        # STEP 6: CALCULATE MONEYNESS AND SPREAD
        # ----------------------------------------------------

        moneyness = strike / stock_price

        relative_spread = (
            ask - bid
        ) / market_price

        # ----------------------------------------------------
        # STEP 7: PROCESS OPTION LAST-TRADE TIMESTAMP
        # ----------------------------------------------------

        # lastTradeDate identifies the most recent reported
        # trade, not the time the bid/ask quote was updated.
        option_last_trade = normalize_timestamp(
            row.get("lastTradeDate")
        )

        option_last_trade_age_hours = (
            calculate_observation_age_hours(
                option_last_trade,
                retrieval_timestamp
            )
        )

        # ----------------------------------------------------
        # STEP 8: STORE OPTION RECORD
        # ----------------------------------------------------

        results.append({
            "Ticker": ticker_symbol,
            "UnderlyingPrice": stock_price,
            "Expiration": expiration_date,
            "Strike": strike,
            "Moneyness": round(moneyness, 6),
            "Bid": bid,
            "Ask": ask,
            "RelativeSpread": round(
                relative_spread, 6
            ),
            "MidPrice": round(
                market_price, 4
            ),
            "ImpliedVolatility": round(
                iv * 100.0, 4
            ),
            "TimeToExpiration": T,
            "RetrievedAtUTC": retrieval_time_iso,
            "UnderlyingObservationAtUTC": underlying_timestamp,
            "UnderlyingObservationAgeHours": underlying_age_hours,
            "OptionLastTradeAtUTC": option_last_trade,
            "OptionLastTradeAgeHours": option_last_trade_age_hours
        })

    # --------------------------------------------------------
    # STEP 9: RETURN STRUCTURED DATA
    # --------------------------------------------------------

    return pd.DataFrame(
        results,
        columns=[
            "Ticker",
            "UnderlyingPrice",
            "Expiration",
            "Strike",
            "Moneyness",
            "Bid",
            "Ask",
            "RelativeSpread",
            "MidPrice",
            "ImpliedVolatility",
            "TimeToExpiration",
            "RetrievedAtUTC",
            "UnderlyingObservationAtUTC",
            "UnderlyingObservationAgeHours",
            "OptionLastTradeAtUTC",
            "OptionLastTradeAgeHours"
        ]
    )


# ============================================================
# RUN MODULE DIRECTLY
# ============================================================

if __name__ == "__main__":

    df = fetch_option_chain(
        ticker_symbol="SPY",
        risk_free_rate=0.045,
        dividend_yield=0.0,
        minimum_days_to_expiry=7
    )

    print(
        "\n--- SPY Implied Volatility Results ---"
    )

    if df.empty:
        print(
            "No valid option quotes were found."
        )

    else:
        print(
            df.head(10).to_string(index=False)
        )