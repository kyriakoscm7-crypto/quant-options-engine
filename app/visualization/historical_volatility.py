"""Historical volatility from explicitly supplied daily closing prices.

No market-data fetching. IV cannot be derived from stock prices alone.
"""
from io import BytesIO
import math

import numpy as np
import pandas as pd

ANNUALIZATION_DAYS = 252
MAX_CSV_BYTES = 2_000_000
MIN_RETURNS = 20


def historical_volatility_from_csv(contents: bytes) -> pd.DataFrame:
    """Return dated 20D/60D annualized realized volatility in percentage units.

    Require a daily adjusted-close-compatible, date-indexed user CSV. Never
    guess a symbol or use unadjusted close across stock splits silently.
    """
    if not isinstance(contents, bytes) or not contents or len(contents) > MAX_CSV_BYTES:
        raise ValueError("Upload a nonempty CSV smaller than 2 MB.")
    try:
        frame = pd.read_csv(BytesIO(contents))
    except (UnicodeError, pd.errors.ParserError, ValueError) as exc:
        raise ValueError("Could not read the daily-price CSV.") from exc
    if not {"Date", "Close"}.issubset(frame.columns):
        raise ValueError("CSV needs Date and Close columns (adjusted daily closing prices).")
    if len(frame) > 10000 or len(frame) < MIN_RETURNS + 1:
        raise ValueError("Provide at least 21 and at most 10,000 daily closing prices.")
    dates = pd.to_datetime(frame["Date"], errors="coerce", utc=True)
    prices = pd.to_numeric(frame["Close"], errors="coerce")
    if dates.isna().any() or prices.isna().any():
        raise ValueError("CSV has invalid dates or closing prices.")
    if (~np.isfinite(prices.to_numpy(dtype=float))).any() or (prices <= 0).any():
        raise ValueError("Closing prices must be positive finite numbers.")
    if dates.duplicated().any():
        raise ValueError("Duplicate dates in CSV; include one daily close per session.")
    if not dates.is_monotonic_increasing:
        raise ValueError("Sort daily prices by Date, oldest to newest.")
    if (dates.dt.dayofweek >= 5).any():
        raise ValueError("CSV must contain trading-session dates, not weekends.")
    daily = np.log(prices / prices.shift(1))
    output = pd.DataFrame({"Date": dates, "Close": prices})
    for lookback in (20, 60):
        output[f"HV{lookback}"] = (
            daily.rolling(lookback, min_periods=lookback).std(ddof=1)
            * math.sqrt(ANNUALIZATION_DAYS) * 100
        )
    return output


def latest_hv(frame: pd.DataFrame, window: int) -> float | None:
    """Latest available measurement, or None if insufficient observations."""
    if window not in (20, 60):
        raise ValueError("Unsupported volatility window")
    series = frame[f"HV{window}"].dropna()
    return None if series.empty else float(series.iloc[-1])
