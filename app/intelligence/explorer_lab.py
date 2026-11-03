"""Deterministic fictional research paths. No symbols or provider dependencies."""

import numpy as np
import pandas as pd


def research_paths(annual_return: float, volatility: float, correlation: float,
                   seed: int = 17, observations: int = 253) -> pd.DataFrame:
    """Geometric Brownian paths; drift is expected simple annualized growth."""
    values = (annual_return, volatility, correlation)
    if not all(np.isfinite(values)) or annual_return <= -1 or volatility <= 0:
        raise ValueError("Use finite drift > -1 and positive volatility")
    if not -1 <= correlation <= 1 or observations < 30:
        raise ValueError("Invalid correlation or observation count")
    rng = np.random.default_rng(seed)
    z = rng.standard_normal((observations - 1, 2))
    shocks = correlation * z[:, 0] + np.sqrt(1 - correlation**2) * z[:, 1]
    a = (np.log1p(annual_return) - volatility**2 / 2) / 252 + volatility / np.sqrt(252) * shocks
    b = (np.log1p(0.06) - 0.16**2 / 2) / 252 + 0.16 / np.sqrt(252) * z[:, 0]
    return pd.DataFrame({
        "Model A": 100 * np.exp(np.r_[0, np.cumsum(a)]),
        "Model B": 100 * np.exp(np.r_[0, np.cumsum(b)]),
    })


def portfolio_path(paths: pd.DataFrame, weight: float) -> pd.Series:
    """Buy-and-hold blend of normalized paths; no periodic rebalancing."""
    if not np.isfinite(weight) or not 0 <= weight <= 1:
        raise ValueError("Weight must be between zero and one")
    normalized = paths / paths.iloc[0]
    return 100 * (weight * normalized.iloc[:, 0] + (1 - weight) * normalized.iloc[:, 1])
