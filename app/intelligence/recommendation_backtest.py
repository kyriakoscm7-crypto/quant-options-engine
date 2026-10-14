"""
Quant Intelligence — Recommendation Score Backtesting.

Evaluates whether historical technical scores were associated with
subsequent returns.

Research only. Does not establish a tradable investment strategy.
"""

import numpy as np
import pandas as pd

from app.intelligence.recommendation_engine import assess_stock


def backtest_recommendations(
    history: pd.DataFrame,
    horizons: tuple[int, ...] = (5, 20, 60),
    step: int = 20,
) -> pd.DataFrame:
    """
    Calculate historical scores without using future prices.

    Each observation:
      1. Scores prices available through date t.
      2. Measures actual returns from t to t+h.
    """

    if "Close" not in history.columns:
        raise ValueError("History must contain a Close column.")

    if step < 1:
        raise ValueError("step must be positive.")

    if not horizons or any(h < 1 for h in horizons):
        raise ValueError("horizons must contain positive integers.")

    close = pd.to_numeric(
        history["Close"], errors="coerce"
    ).replace([np.inf, -np.inf], np.nan).dropna()

    if (close <= 0).any():
        raise ValueError("Closing prices must be positive.")

    max_horizon = max(horizons)

    if len(close) < 252 + max_horizon:
        raise ValueError("Not enough historical prices for backtesting.")

    results = []

    for end in range(251, len(close) - max_horizon, step):
        past = pd.DataFrame({
            "Close": close.iloc[:end + 1].to_numpy()
        })

        assessment = assess_stock(past)

        if assessment.score is None:
            continue

        current_price = float(close.iloc[end])

        row = {
            "observation": end,
            "score": assessment.score,
            "recommendation": assessment.recommendation,
        }

        for horizon in horizons:
            future_price = float(close.iloc[end + horizon])

            row[f"return_{horizon}d"] = (
                future_price / current_price - 1
            )

        results.append(row)

    return pd.DataFrame(results)


def summarize_backtest(
    results: pd.DataFrame,
    horizons: tuple[int, ...] = (5, 20, 60),
) -> pd.DataFrame:
    """Summarize future returns grouped by historical score range."""

    if results.empty:
        return pd.DataFrame()

    data = results.copy()

    data["score_group"] = pd.cut(
        data["score"],
        bins=[-1, 39, 54, 69, 84, 100],
        labels=[
            "0–39",
            "40–54",
            "55–69",
            "70–84",
            "85–100",
        ],
    )

    summary = []

    for group, subset in data.groupby("score_group", observed=True):
        row = {
            "score_group": str(group),
            "observations": len(subset),
        }

        for horizon in horizons:
            column = f"return_{horizon}d"

            if column not in subset.columns:
                continue

            returns = subset[column].dropna()

            if returns.empty:
                continue

            row[f"average_{horizon}d_pct"] = (
                float(returns.mean()) * 100
            )

            row[f"positive_{horizon}d_pct"] = (
                float((returns > 0).mean()) * 100
            )

        summary.append(row)

    return pd.DataFrame(summary)
