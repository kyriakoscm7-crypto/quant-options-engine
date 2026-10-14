"""Diagnostics for unusual historical stock-price movements."""

import numpy as np
import pandas as pd


def detect_price_anomalies(
    histories: dict[str, pd.DataFrame],
    threshold: float = 0.50,
) -> pd.DataFrame:
    """Find unusually large close-to-close returns.

    A flagged return is not necessarily erroneous. Genuine corporate
    events, speculative trading, and data problems can all trigger it.
    """
    if not 0 < threshold < 1:
        raise ValueError("threshold must be between zero and one.")

    records = []

    for ticker, history in histories.items():
        if "Close" not in history.columns:
            continue

        prices = pd.to_numeric(
            history["Close"],
            errors="coerce",
        ).sort_index()

        if prices.index.has_duplicates:
            raise ValueError(f"Duplicate dates for {ticker}.")

        valid_prices = prices.where(
            np.isfinite(prices) & (prices > 0)
        )

        returns = valid_prices.pct_change(fill_method=None)

        flagged = returns[
            returns.notna() & (returns.abs() >= threshold)
        ]

        for date, daily_return in flagged.items():
            previous_date = prices.index.get_loc(date) - 1

            if previous_date < 0:
                continue

            previous_close = prices.iloc[previous_date]
            current_close = prices.loc[date]

            records.append(
                {
                    "Ticker": ticker,
                    "Date": pd.Timestamp(date),
                    "Previous Close": float(previous_close),
                    "Current Close": float(current_close),
                    "Daily Return (%)": float(daily_return * 100),
                    "Absolute Return (%)": float(abs(daily_return) * 100),
                }
            )

    columns = [
        "Ticker",
        "Date",
        "Previous Close",
        "Current Close",
        "Daily Return (%)",
        "Absolute Return (%)",
    ]

    if not records:
        return pd.DataFrame(columns=columns)

    return (
        pd.DataFrame(records)
        .sort_values(
            ["Absolute Return (%)", "Ticker", "Date"],
            ascending=[False, True, True],
        )
        .reset_index(drop=True)
    )
