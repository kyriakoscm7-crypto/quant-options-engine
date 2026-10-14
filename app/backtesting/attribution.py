"""Portfolio valuation-change diagnostics for backtest auditing.

This module does not calculate realized or unrealized trading P&L.
Changes in position values can include purchases, sales, and price changes.
"""

import ast
import math

import pandas as pd


def _parse_positions(value: object) -> dict[str, float]:
    """Validate a portfolio position-value mapping."""
    if isinstance(value, str):
        value = ast.literal_eval(value)

    if not isinstance(value, dict):
        raise ValueError("Position Values must be a dictionary.")

    positions = {}

    for ticker, amount in value.items():
        number = float(amount)

        if not math.isfinite(number) or number < 0:
            raise ValueError(f"Invalid position value for {ticker}")

        positions[str(ticker)] = number

    return positions


def analyze_position_changes(results: pd.DataFrame) -> pd.DataFrame:
    """Identify large day-to-day changes in recorded position values.

    Position-value changes are NOT investment P&L because trades can
    occur between observations.
    """
    required = {"Date", "Portfolio Value", "Cash", "Position Values"}

    missing = required - set(results.columns)

    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    if results.empty:
        return pd.DataFrame(
            columns=[
                "Date",
                "Ticker",
                "Previous Position Value",
                "Current Position Value",
                "Position Value Change ($)",
                "Portfolio Change ($)",
                "Possible Trading Activity",
            ]
        )

    ordered = results.copy()
    ordered["Date"] = pd.to_datetime(ordered["Date"])

    if ordered["Date"].isna().any():
        raise ValueError("Invalid portfolio dates.")

    if ordered["Date"].duplicated().any():
        raise ValueError("Duplicate portfolio dates.")

    ordered = ordered.sort_values("Date").reset_index(drop=True)

    records = []

    for index in range(1, len(ordered)):
        previous = ordered.iloc[index - 1]
        current = ordered.iloc[index]

        previous_positions = _parse_positions(
            previous["Position Values"]
        )

        current_positions = _parse_positions(
            current["Position Values"]
        )

        previous_total = float(previous["Portfolio Value"])
        current_total = float(current["Portfolio Value"])

        previous_cash = float(previous["Cash"])
        current_cash = float(current["Cash"])

        if not all(
            math.isfinite(value)
            for value in (
                previous_total,
                current_total,
                previous_cash,
                current_cash,
            )
        ):
            raise ValueError("Non-finite portfolio value or cash.")

        if previous_total <= 0 or current_total <= 0:
            raise ValueError("Portfolio values must be positive.")

        if previous_cash < -1e-7 or current_cash < -1e-7:
            raise ValueError("Cash cannot be negative.")

        tickers = sorted(
            set(previous_positions) | set(current_positions)
        )

        holdings_changed = (
            set(previous_positions) != set(current_positions)
        )

        cash_changed = not math.isclose(
            previous_cash,
            current_cash,
            rel_tol=1e-9,
            abs_tol=1e-6,
        )

        possible_trading = holdings_changed or cash_changed

        portfolio_change = current_total - previous_total

        for ticker in tickers:
            previous_value = previous_positions.get(ticker, 0.0)
            current_value = current_positions.get(ticker, 0.0)

            records.append(
                {
                    "Date": current["Date"],
                    "Ticker": ticker,
                    "Previous Position Value": previous_value,
                    "Current Position Value": current_value,
                    "Position Value Change ($)": (
                        current_value - previous_value
                    ),
                    "Portfolio Change ($)": portfolio_change,
                    "Possible Trading Activity": possible_trading,
                }
            )

    return pd.DataFrame(records)


def largest_position_changes(
    changes: pd.DataFrame,
    top_n: int = 20,
) -> pd.DataFrame:
    """Return the largest absolute recorded position-value changes."""
    if top_n < 1:
        raise ValueError("top_n must be positive.")

    if changes.empty:
        return changes.copy()

    required = {"Position Value Change ($)"}

    if not required.issubset(changes.columns):
        raise ValueError("Missing position-value change column.")

    return (
        changes.assign(
            _absolute_change=changes[
                "Position Value Change ($)"
            ].abs()
        )
        .sort_values(
            "_absolute_change",
            ascending=False,
            kind="stable",
        )
        .head(top_n)
        .drop(columns="_absolute_change")
        .reset_index(drop=True)
    )
