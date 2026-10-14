"""Portfolio concentration analysis for historical backtests."""

from __future__ import annotations

import pandas as pd


def analyze_concentration(
    results: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate daily portfolio concentration from recorded positions."""

    required = {"Date", "Portfolio Value", "Position Values"}

    missing = required - set(results.columns)

    if missing:
        raise ValueError(
            f"Missing required columns: {sorted(missing)}"
        )

    records = []

    for _, row in results.iterrows():
        portfolio_value = float(row["Portfolio Value"])
        positions = row["Position Values"]

        if portfolio_value <= 0:
            raise ValueError("Portfolio value must be positive.")

        if not isinstance(positions, dict):
            raise TypeError("Position Values must be a dictionary.")

        weights = {
            ticker: float(value) / portfolio_value
            for ticker, value in positions.items()
        }

        if weights:
            largest_ticker = max(weights, key=weights.get)
            largest_weight = weights[largest_ticker]
            top_three_weight = sum(
                sorted(weights.values(), reverse=True)[:3]
            )
            hhi = sum(weight**2 for weight in weights.values())
        else:
            largest_ticker = None
            largest_weight = 0.0
            top_three_weight = 0.0
            hhi = 0.0

        records.append(
            {
                "Date": row["Date"],
                "Largest Stock": largest_ticker,
                "Largest Weight (%)": largest_weight * 100,
                "Top 3 Weight (%)": top_three_weight * 100,
                "Concentration HHI": hhi,
                "Above 20%": largest_weight > 0.20,
                "Above 30%": largest_weight > 0.30,
                "Above 50%": largest_weight > 0.50,
            }
        )

    return pd.DataFrame(records)
