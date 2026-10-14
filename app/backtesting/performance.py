"""Performance calculations for historical investment simulations."""

from __future__ import annotations

import numpy as np
import pandas as pd


def calculate_performance(
    values: pd.Series,
    initial_capital: float = 10_000.0,
) -> dict[str, float]:
    """Calculate performance relative to the actual initial investment."""

    if initial_capital <= 0:
        raise ValueError("Initial capital must be positive.")

    values = pd.to_numeric(values, errors="coerce").dropna()
    values = values.sort_index()

    if len(values) < 2:
        raise ValueError("At least two portfolio observations are required.")

    if (values <= 0).any():
        raise ValueError("Portfolio values must be positive.")

    if not isinstance(values.index, pd.DatetimeIndex):
        raise ValueError("Portfolio values must have a DatetimeIndex.")

    if values.index.has_duplicates:
        raise ValueError("Portfolio dates must be unique.")

    final_value = float(values.iloc[-1])

    total_return = final_value / initial_capital - 1.0

    years = (
        values.index[-1] - values.index[0]
    ).total_seconds() / (365.25 * 24 * 60 * 60)

    if years <= 0:
        raise ValueError("Portfolio period must be positive.")

    cagr = (
        final_value / initial_capital
    ) ** (1.0 / years) - 1.0

    daily_returns = values.pct_change().dropna()

    volatility = (
        float(daily_returns.std(ddof=1) * np.sqrt(252))
        if len(daily_returns) > 1
        else float("nan")
    )

    equity_curve = pd.concat(
        [
            pd.Series(
                [initial_capital],
                index=[values.index[0] - pd.Timedelta(nanoseconds=1)],
            ),
            values,
        ]
    )

    drawdowns = equity_curve / equity_curve.cummax() - 1.0

    return {
        "initial_capital": float(initial_capital),
        "final_value": final_value,
        "total_return_pct": float(total_return * 100),
        "cagr_pct": float(cagr * 100),
        "annualized_volatility_pct": float(volatility * 100),
        "max_drawdown_pct": float(drawdowns.min() * 100),
    }
