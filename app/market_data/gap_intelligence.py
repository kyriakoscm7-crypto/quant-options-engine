"""
Gap and volume intelligence for daily stock market data.

This module provides descriptive historical market signals.
It does not predict future returns or trading profitability.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class GapVolumeSummary:
    ticker: str
    observation_count: int
    latest_date: pd.Timestamp
    opening_gap_pct: float
    relative_volume: float
    gap_z_score: float | None
    gap_direction: str


def calculate_gap_volume_signals(
    history: pd.DataFrame,
    ticker: str,
    lookback: int = 20,
    latest_session_complete: bool = False,
) -> GapVolumeSummary:
    """
    Analyze the latest eligible daily session.

    The current/latest row is excluded by default because
    it may represent an incomplete trading session.

    Relative volume uses the preceding completed sessions.

    Gap significance uses only preceding historical gaps.
    """

    if not isinstance(history, pd.DataFrame):
        raise ValueError("History must be a DataFrame.")

    if not isinstance(lookback, int) or isinstance(lookback, bool):
        raise ValueError("Lookback must be an integer.")

    if lookback < 5:
        raise ValueError("Lookback must be at least 5.")

    required = {"Date", "Open", "Close", "Volume"}

    if not required.issubset(history.columns):
        raise ValueError(
            "History must contain Date, Open, Close, and Volume."
        )

    frame = history[
        ["Date", "Open", "Close", "Volume"]
    ].copy()

    frame["Date"] = pd.to_datetime(
        frame["Date"],
        utc=True,
        errors="raise",
    )

    if frame["Date"].isna().any():
        raise ValueError("History contains missing dates.")

    if frame["Date"].duplicated().any():
        raise ValueError("History contains duplicate dates.")

    frame = frame.sort_values("Date").reset_index(drop=True)

    for column in ["Open", "Close", "Volume"]:
        frame[column] = pd.to_numeric(
            frame[column],
            errors="raise",
        )

        if not np.isfinite(frame[column].to_numpy()).all():
            raise ValueError(
                f"History contains non-finite {column} values."
            )

    if (frame["Open"] <= 0).any():
        raise ValueError("Opening prices must be positive.")

    if (frame["Close"] <= 0).any():
        raise ValueError("Closing prices must be positive.")

    if (frame["Volume"] < 0).any():
        raise ValueError("Volume cannot be negative.")

    if not latest_session_complete:
        frame = frame.iloc[:-1].copy()

    minimum_rows = lookback + 2

    if len(frame) < minimum_rows:
        raise ValueError(
            f"At least {minimum_rows} completed historical "
            "rows are required."
        )

    frame["Previous Close"] = frame["Close"].shift(1)

    frame["Gap (%)"] = (
        frame["Open"] / frame["Previous Close"] - 1
    ) * 100

    latest = frame.iloc[-1]

    historical = frame.iloc[-(lookback + 1):-1]

    historical_gaps = historical["Gap (%)"].dropna()

    if len(historical_gaps) < lookback:
        raise ValueError(
            "Insufficient historical gaps for analysis."
        )

    average_volume = historical["Volume"].mean()

    if average_volume <= 0:
        raise ValueError(
            "Historical average volume must be positive."
        )

    relative_volume = (
        float(latest["Volume"]) / float(average_volume)
    )

    gap_std = float(historical_gaps.std(ddof=1))

    if gap_std > 0:
        gap_z_score = (
            float(latest["Gap (%)"])
            - float(historical_gaps.mean())
        ) / gap_std
    else:
        gap_z_score = None

    gap = float(latest["Gap (%)"])

    if gap > 0:
        direction = "Gap Up"
    elif gap < 0:
        direction = "Gap Down"
    else:
        direction = "No Gap"

    return GapVolumeSummary(
        ticker=ticker.strip().upper(),
        observation_count=len(frame),
        latest_date=pd.Timestamp(latest["Date"]),
        opening_gap_pct=gap,
        relative_volume=relative_volume,
        gap_z_score=gap_z_score,
        gap_direction=direction,
    )
