"""
Quant Intelligence — Technical Research Scoring Engine.

Scores describe historical technical conditions, not the probability
of positive future returns. Predictive validity is not established.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class InvestmentAssessment:
    score: int | None
    recommendation: str
    outlook: str
    risk: str
    reliability: str
    reasons: tuple[str, ...]


def assess_stock(history: pd.DataFrame) -> InvestmentAssessment:
    """Calculate a continuous, risk-aware technical research score."""

    if "Close" not in history.columns:
        raise ValueError("History must contain a Close column.")

    close = pd.to_numeric(
        history["Close"], errors="coerce"
    ).replace([np.inf, -np.inf], np.nan).dropna()

    if len(close) < 252:
        return InvestmentAssessment(
            score=None,
            recommendation="INSUFFICIENT EVIDENCE",
            outlook="Unknown",
            risk="Unknown",
            reliability="Insufficient history",
            reasons=("At least 252 valid daily prices are required.",),
        )

    if (close <= 0).any():
        raise ValueError("Closing prices must be positive.")

    # Only use the latest 252 observations for risk measurements.
    close = close.iloc[-252:]
    returns = close.pct_change().dropna()

    latest = float(close.iloc[-1])
    sma50 = float(close.iloc[-50:].mean())
    sma200 = float(close.iloc[-200:].mean())

    volatility = float(returns.std(ddof=1) * np.sqrt(252))

    if not np.isfinite(volatility):
        raise ValueError("Cannot calculate volatility.")

    # Volatility floor avoids unstable division for nearly flat prices.
    safe_volatility = max(volatility, 0.05)

    # 1. Trend strength: risk-normalized distance from moving averages.
    distance200 = latest / sma200 - 1
    distance50 = latest / sma50 - 1

    trend_signal = (
        0.65 * distance200 + 0.35 * distance50
    ) / safe_volatility

    trend_score = 50 + 50 * np.tanh(3.0 * trend_signal)

    # 2. Momentum: returns adjusted for realized volatility.
    return20 = latest / float(close.iloc[-21]) - 1
    return60 = latest / float(close.iloc[-61]) - 1

    momentum_signal = (
        0.4 * return20 + 0.6 * return60
    ) / safe_volatility

    momentum_score = 50 + 50 * np.tanh(4.0 * momentum_signal)

    # 3. Trend consistency: fraction of recent prices above SMA50.
    rolling50 = close.rolling(50).mean()
    recent_close = close.iloc[-60:]
    recent_average = rolling50.iloc[-60:]

    consistency_score = float(
        (recent_close > recent_average).mean() * 100
    )

    # 4. Volatility: continuous penalty for larger fluctuations.
    volatility_score = float(
        100 / (1 + (volatility / 0.35) ** 2)
    )

    # 5. Downside: current drawdown and recent maximum drawdown.
    running_peak = close.cummax()
    drawdowns = close / running_peak - 1

    current_drawdown = abs(float(drawdowns.iloc[-1]))
    maximum_drawdown = abs(float(drawdowns.min()))

    downside_measure = (
        0.6 * current_drawdown + 0.4 * maximum_drawdown
    )

    downside_score = float(
        100 * np.exp(-3.0 * downside_measure)
    )

    # Explicit fixed weights; these are not yet empirically validated.
    weighted_score = (
        0.25 * trend_score
        + 0.25 * momentum_score
        + 0.15 * consistency_score
        + 0.15 * volatility_score
        + 0.20 * downside_score
    )

    score = int(np.clip(np.rint(weighted_score), 0, 100))

    reasons = [
        f"20-day return: {return20:+.1%}.",
        f"60-day return: {return60:+.1%}.",
        f"Annualized historical volatility: {volatility:.1%}.",
        f"Maximum drawdown over 252 observations: "
        f"{maximum_drawdown:.1%}.",
        f"Price relative to 200-day average: {distance200:+.1%}.",
        "Score uses provisional technical weights; "
        "predictive performance has not been validated.",
    ]

    if score >= 85:
        recommendation = "STRONG TECHNICAL SIGNAL"
        outlook = "Bullish"
    elif score >= 70:
        recommendation = "FAVORABLE TECHNICAL SIGNAL"
        outlook = "Bullish"
    elif score >= 55:
        recommendation = "NEUTRAL / MIXED"
        outlook = "Neutral"
    elif score >= 40:
        recommendation = "CAUTION"
        outlook = "Neutral"
    else:
        recommendation = "UNFAVORABLE TECHNICAL SIGNAL"
        outlook = "Bearish"

    if volatility >= 0.60:
        risk = "Very High"
    elif volatility >= 0.40:
        risk = "High"
    elif volatility >= 0.20:
        risk = "Moderate"
    else:
        risk = "Lower Historical Volatility"

    return InvestmentAssessment(
        score=score,
        recommendation=recommendation,
        outlook=outlook,
        risk=risk,
        reliability="Predictive accuracy not yet validated",
        reasons=tuple(reasons),
    )
