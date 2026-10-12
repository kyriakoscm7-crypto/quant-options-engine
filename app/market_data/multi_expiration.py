"""
Multi-Expiration Options Data Collector

Purpose
-------
Collect implied volatility data across multiple option expirations.

This module extends our existing Yahoo Finance market-data pipeline
without modifying the original yahoo_client.py file.

The resulting dataset will be used to construct an interactive
3D implied volatility visualization.
"""

import math
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

from app.market_data.yahoo_client import (
    MARKET_TIMEZONE,
    fetch_option_chain,
)


# ============================================================
# EXPIRATION SELECTION
# ============================================================

def select_expirations(
    expirations: list[str],
    minimum_days_to_expiry: int = 7,
    maximum_expirations: int = 6,
) -> list[str]:
    """
    Select the earliest eligible option expiration dates.

    Parameters
    ----------
    expirations:
        Available expiration dates in YYYY-MM-DD format.

    minimum_days_to_expiry:
        Minimum calendar days until expiration.

    maximum_expirations:
        Maximum number of expiration dates to select.

    Returns
    -------
    list[str]
        Selected expiration dates in chronological order.
    """

    if minimum_days_to_expiry < 0:
        raise ValueError(
            "minimum_days_to_expiry cannot be negative."
        )

    if maximum_expirations < 1:
        raise ValueError(
            "maximum_expirations must be at least 1."
        )

    today = datetime.now(MARKET_TIMEZONE).date()

    minimum_date = today + timedelta(
        days=minimum_days_to_expiry
    )

    eligible = []

    for expiration in expirations:

        expiration_date = datetime.strptime(
            expiration,
            "%Y-%m-%d"
        ).date()

        if expiration_date >= minimum_date:
            eligible.append(expiration)

    # Remove duplicates and sort chronologically.
    eligible = sorted(set(eligible))

    return eligible[:maximum_expirations]


# ============================================================
# MULTI-EXPIRATION COLLECTION
# ============================================================

def fetch_multiple_expirations(
    ticker_symbol: str = "SPY",
    risk_free_rate: float = 0.045,
    dividend_yield: float = 0.0,
    minimum_days_to_expiry: int = 7,
    maximum_expirations: int = 6,
    maximum_relative_spread: float = 0.30,
) -> pd.DataFrame:
    """
    Collect option-chain data across multiple expiration dates.

    Returns a combined DataFrame containing the same columns
    as our existing fetch_option_chain() function.

    Each expiration contributes its own option observations.
    """

    print(
        f"\nFetching multiple expirations for {ticker_symbol}..."
    )

    ticker = yf.Ticker(ticker_symbol)

    available_expirations = ticker.options

    if not available_expirations:
        raise RuntimeError(
            "No option expiration dates available."
        )

    selected_expirations = select_expirations(
        expirations=list(available_expirations),
        minimum_days_to_expiry=minimum_days_to_expiry,
        maximum_expirations=maximum_expirations,
    )

    if not selected_expirations:
        raise RuntimeError(
            "No eligible option expirations available."
        )

    print("\nSelected expirations:")

    for expiration in selected_expirations:
        print(f"  {expiration}")

    all_data = []

    # --------------------------------------------------------
    # COLLECT EACH EXPIRATION
    # --------------------------------------------------------

    for expiration in selected_expirations:

        print(
            f"\nProcessing expiration: {expiration}"
        )

        # IMPORTANT:
        # Our current fetch_option_chain() selects the earliest
        # eligible expiration based on minimum_days_to_expiry.
        #
        # To request a particular expiration, we calculate
        # the calendar-day offset from today's date.

        today = datetime.now(MARKET_TIMEZONE).date()

        target_date = datetime.strptime(
            expiration,
            "%Y-%m-%d"
        ).date()

        days_until_expiration = (
            target_date - today
        ).days

        try:

            df = fetch_option_chain(
                ticker_symbol=ticker_symbol,
                risk_free_rate=risk_free_rate,
                dividend_yield=dividend_yield,
                minimum_days_to_expiry=days_until_expiration,
                maximum_relative_spread=maximum_relative_spread,
            )

            if df.empty:
                print(
                    "No valid quotes for this expiration."
                )
                continue

            # Ensure the returned data corresponds to the
            # expiration we're currently processing.
            #
            # This is necessary because fetch_option_chain()
            # selects the first eligible expiration.

            returned_expiration = str(
                df["Expiration"].iloc[0]
            )

            if returned_expiration != expiration:

                print(
                    "Skipping unexpected expiration: "
                    f"{returned_expiration}"
                )

                continue

            all_data.append(df)

            print(
                f"Collected {len(df)} valid option quotes."
            )

        except (RuntimeError, ValueError) as error:

            print(
                f"Skipping {expiration}: {error}"
            )

    # --------------------------------------------------------
    # COMBINE RESULTS
    # --------------------------------------------------------

    if not all_data:
        raise RuntimeError(
            "No valid option data collected."
        )

    combined = pd.concat(
        all_data,
        ignore_index=True
    )

    combined = combined.sort_values(
        by=["TimeToExpiration", "Strike"]
    ).reset_index(drop=True)

    print(
        f"\nTotal valid option observations: {len(combined)}"
    )

    print(
        "Expirations collected: "
        f"{combined['Expiration'].nunique()}"
    )

    return combined


# ============================================================
# RUN MODULE DIRECTLY
# ============================================================

if __name__ == "__main__":

    df = fetch_multiple_expirations(
        ticker_symbol="SPY",
        risk_free_rate=0.045,
        dividend_yield=0.0,
        minimum_days_to_expiry=7,
        maximum_expirations=6,
        maximum_relative_spread=0.30,
    )

    print(
        "\n--- MULTI-EXPIRATION DATA SUMMARY ---"
    )

    summary = df.groupby(
        "Expiration"
    ).agg(
        OptionCount=("Strike", "count"),
        MinimumStrike=("Strike", "min"),
        MaximumStrike=("Strike", "max"),
        MinimumIV=("ImpliedVolatility", "min"),
        MaximumIV=("ImpliedVolatility", "max"),
    )

    print(
        summary.to_string()
    )

    print(
        "\n--- FIRST 10 OBSERVATIONS ---"
    )

    print(
        df.head(10).to_string(index=False)
    )