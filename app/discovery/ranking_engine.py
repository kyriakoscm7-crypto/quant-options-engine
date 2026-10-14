"""Technical research rankings for multiple investment horizons."""

from __future__ import annotations

import math
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
import yfinance as yf

HORIZONS = {
    "5 Days": {
        "momentum": 5,
        "trend": 10,
        "history": "3mo",
    },
    "1 Month": {
        "momentum": 21,
        "trend": 50,
        "history": "6mo",
    },
    "1 Year": {
        "momentum": 126,
        "trend": 200,
        "history": "2y",
    },
}


def _bounded(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _score_ticker(ticker: str, horizon: str) -> dict | None:
    """Calculate a transparent technical-strength research score."""

    config = HORIZONS[horizon]

    try:
        history = yf.Ticker(ticker).history(
            period=config["history"],
            interval="1d",
            auto_adjust=True,
        )

        if history.empty:
            return None

        closes = pd.to_numeric(
            history["Close"],
            errors="coerce",
        ).dropna()

        volumes = pd.to_numeric(
            history["Volume"],
            errors="coerce",
        ).reindex(closes.index).fillna(0)

        momentum_days = config["momentum"]
        trend_days = config["trend"]

        if len(closes) < max(momentum_days + 1, trend_days):
            return None

        price = float(closes.iloc[-1])

        if not math.isfinite(price) or price <= 0:
            return None

        reference_price = float(
            closes.iloc[-momentum_days - 1]
        )

        momentum_return = (
            price / reference_price - 1
        ) * 100

        moving_average = float(
            closes.tail(trend_days).mean()
        )

        trend_distance = (
            price / moving_average - 1
        ) * 100

        daily_returns = closes.pct_change().dropna()

        volatility = float(
            daily_returns.tail(63).std() * np.sqrt(252) * 100
        )

        if not math.isfinite(volatility):
            return None

        average_volume = float(
            volumes.tail(20).mean()
        )

        momentum_score = _bounded(
            50 + momentum_return * 2.0,
            0,
            100,
        )

        trend_score = _bounded(
            50 + trend_distance * 2.0,
            0,
            100,
        )

        risk_score = _bounded(
            100 - volatility,
            0,
            100,
        )

        if horizon == "5 Days":
            score = (
                0.55 * momentum_score
                + 0.30 * trend_score
                + 0.15 * risk_score
            )

        elif horizon == "1 Month":
            score = (
                0.45 * momentum_score
                + 0.40 * trend_score
                + 0.15 * risk_score
            )

        else:
            score = (
                0.35 * momentum_score
                + 0.45 * trend_score
                + 0.20 * risk_score
            )

        return {
            "ticker": ticker,
            "score": round(score, 1),
            "price": round(price, 2),
            "momentum_return": round(momentum_return, 2),
            "trend_distance": round(trend_distance, 2),
            "volatility": round(volatility, 2),
            "average_volume": round(average_volume),
            "momentum_score": round(momentum_score, 1),
            "trend_score": round(trend_score, 1),
            "risk_score": round(risk_score, 1),
            "data_as_of": str(closes.index[-1].date()),
        }

    except Exception:
        return None


def rank_companies(
    tickers: list[str],
    horizon: str,
    max_workers: int = 4,
) -> list[dict]:
    """Rank stocks using current daily price history."""

    if horizon not in HORIZONS:
        raise ValueError(f"Unsupported horizon: {horizon}")

    tickers = list(dict.fromkeys(tickers))

    if not tickers:
        return []

    results = []

    with ThreadPoolExecutor(
        max_workers=max_workers
    ) as executor:
        futures = {
            executor.submit(
                _score_ticker,
                ticker,
                horizon,
            ): ticker
            for ticker in tickers
        }

        for future in as_completed(futures):
            result = future.result()

            if result is not None:
                results.append(result)

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    for index, result in enumerate(results, start=1):
        result["rank"] = index

    return results
