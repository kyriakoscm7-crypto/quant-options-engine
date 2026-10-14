"""Alternative historical stock-ranking strategies."""

from __future__ import annotations

import numpy as np
import pandas as pd


def alternative_rankings(
    histories: dict[str, pd.DataFrame],
    as_of: pd.Timestamp,
    horizon: str,
    method: str = "momentum",
) -> pd.DataFrame:
    """Rank stocks using historical momentum or momentum plus trend."""

    if method not in {"momentum", "momentum_trend"}:
        raise ValueError(f"Unknown ranking method: {method}")

    rows = []
    cutoff = pd.Timestamp(as_of) - pd.Timedelta(days=7)

    for ticker, history in histories.items():
        historical = history.loc[
            history.index <= as_of
        ].sort_index()

        if len(historical) < 253:
            continue

        if pd.Timestamp(historical.index[-1]) < cutoff:
            continue

        closes = pd.to_numeric(
            historical["Close"], errors="coerce"
        )

        if closes.isna().any() or (closes <= 0).any():
            continue

        momentum = float(
            closes.iloc[-1] / closes.iloc[-253] - 1.0
        )

        ma50 = float(closes.iloc[-50:].mean())
        ma200 = float(closes.iloc[-200:].mean())

        trend = ma50 / ma200 - 1.0

        if not (
            np.isfinite(momentum)
            and np.isfinite(trend)
        ):
            continue

        rows.append(
            {
                "ticker": ticker,
                "momentum": momentum,
                "trend": trend,
            }
        )

    if not rows:
        return pd.DataFrame(columns=["ticker", "score", "horizon"])

    rankings = pd.DataFrame(rows)

    if method == "momentum":
        rankings["score"] = rankings["momentum"]
    else:
        momentum_rank = rankings["momentum"].rank(pct=True)
        trend_rank = rankings["trend"].rank(pct=True)

        rankings["score"] = (
            0.5 * momentum_rank
            + 0.5 * trend_rank
        )

    rankings["horizon"] = horizon

    return (
        rankings.sort_values(
            ["score", "ticker"],
            ascending=[False, True],
        )
        .reset_index(drop=True)
    )


def momentum_rankings(histories, as_of, horizon):
    """Rank stocks using historical 12-month momentum."""
    return alternative_rankings(
        histories, as_of, horizon, method="momentum"
    )


def momentum_trend_rankings(histories, as_of, horizon):
    """Rank stocks using equal-weight momentum and trend percentiles."""
    return alternative_rankings(
        histories, as_of, horizon, method="momentum_trend"
    )
