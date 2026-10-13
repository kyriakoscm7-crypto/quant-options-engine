"""Beginner-friendly descriptions of observed market momentum."""

import math


def classify_market_signal(
    one_month_momentum: object,
    three_month_momentum: object,
    ranking_status: str = "Ranked",
) -> tuple[str, str]:
    """Classify historical momentum, not expected future returns."""

    if ranking_status != "Ranked":
        return (
            "⚪ Unavailable",
            "Insufficient data for a reliable momentum signal.",
        )

    try:
        one_month = float(one_month_momentum)
        three_month = float(three_month_momentum)
    except (TypeError, ValueError):
        return (
            "⚪ Unavailable",
            "Momentum data is missing or invalid.",
        )

    if not (
        math.isfinite(one_month)
        and math.isfinite(three_month)
    ):
        return (
            "⚪ Unavailable",
            "Momentum data is missing or invalid.",
        )

    if one_month > 0 and three_month > 0:
        return (
            "🟢 Bullish",
            "Price momentum is positive over both 1 and 3 months.",
        )

    if one_month < 0 and three_month < 0:
        return (
            "🔴 Bearish",
            "Price momentum is negative over both 1 and 3 months.",
        )

    return (
        "🟡 Mixed",
        "Recent momentum is mixed or flat.",
    )
