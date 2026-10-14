"""Plain-English interpretations of historical risk metrics."""

from __future__ import annotations

import math


def _valid(value):
    """Return a finite number or None."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def interpret_volatility(value):
    value = _valid(value)
    if value is None:
        return "Not enough data to assess historical volatility."

    if value < 15:
        return "This stock has shown relatively small historical price swings."
    if value < 30:
        return "This stock has shown moderate historical price swings."
    if value < 50:
        return "This stock has shown relatively large historical price swings."

    return "This stock has experienced very large historical price swings."


def interpret_drawdown(value):
    value = _valid(value)
    if value is None:
        return "Not enough data to measure the largest historical decline."

    return (
        f"At its worst, this stock fell {abs(value):.1f}% "
        "from a previous high during the measured period."
    )


def interpret_sharpe(value):
    value = _valid(value)
    if value is None:
        return "Not enough data to assess historical risk-adjusted returns."

    if value < 0:
        return "Historical returns were negative relative to the assumed risk-free rate."
    if value < 1:
        return "Historical returns were modest relative to the stock's volatility."
    if value < 2:
        return "Historical returns were relatively strong compared with volatility."

    return "Historical returns were very strong relative to volatility."


def interpret_beta(value):
    value = _valid(value)
    if value is None:
        return "Not enough overlapping market data to estimate sensitivity."

    if value < 0:
        return (
            "This stock has historically tended to move opposite "
            "to SPY's daily movements."
        )

    if value < 0.9:
        return (
            "This stock has historically been less sensitive "
            "to SPY's daily movements."
        )

    if value <= 1.1:
        return (
            "This stock has historically shown similar sensitivity "
            "to SPY's daily movements."
        )

    return (
        f"This stock has historically been about "
        f"{(value - 1) * 100:.0f}% more sensitive "
        "to SPY's daily movements."
    )


def interpret_correlation(value):
    value = _valid(value)
    if value is None:
        return "Not enough overlapping data to assess market correlation."

    if value >= 0.7:
        return "This stock's daily returns have generally moved closely with SPY."
    if value >= 0.3:
        return "This stock's daily returns have shown some tendency to follow SPY."
    if value > -0.3:
        return "This stock's daily returns have shown little consistent relationship with SPY."
    if value > -0.7:
        return "This stock's daily returns have often moved opposite to SPY."

    return "This stock's daily returns have generally moved opposite to SPY."


def interpret_risk_metrics(metrics):
    """Return one-sentence interpretations for all five metrics."""
    return {
        "annualized_volatility_pct": interpret_volatility(
            metrics.get("annualized_volatility_pct")
        ),
        "maximum_drawdown_pct": interpret_drawdown(
            metrics.get("maximum_drawdown_pct")
        ),
        "sharpe_ratio": interpret_sharpe(
            metrics.get("sharpe_ratio")
        ),
        "beta_vs_spy": interpret_beta(
            metrics.get("beta_vs_spy")
        ),
        "correlation_vs_spy": interpret_correlation(
            metrics.get("correlation_vs_spy")
        ),
    }
