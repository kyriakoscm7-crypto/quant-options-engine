"""Batch-based ranking pipeline for Quant Discovery."""

from __future__ import annotations

import argparse
import math
import sqlite3
from datetime import UTC, datetime

import numpy as np
import pandas as pd
import yfinance as yf

from app.discovery.database import DATABASE_PATH, initialize_database

HORIZONS = {
    "5 Days": {"momentum": 5, "trend": 10},
    "1 Month": {"momentum": 21, "trend": 50},
    "1 Year": {"momentum": 126, "trend": 200},
}

METHODOLOGY = "technical_v2"

MIN_DOLLAR_VOLUME = 1_000_000


def initialize_rankings():
    initialize_database()

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS ranking_cache (
                ticker TEXT NOT NULL,
                horizon TEXT NOT NULL,
                score REAL NOT NULL,
                momentum_return REAL,
                trend_distance REAL,
                volatility REAL,
                average_dollar_volume REAL,
                price REAL,
                data_as_of TEXT,
                calculated_at TEXT NOT NULL,
                methodology TEXT NOT NULL,
                PRIMARY KEY (ticker, horizon, methodology)
            )
            """
        )


def get_tickers(limit=None):
    with sqlite3.connect(DATABASE_PATH) as connection:
        query = """
            SELECT ticker
            FROM companies
            ORDER BY ticker
        """

        if limit is not None:
            query += f" LIMIT {int(limit)}"

        return [
            row[0]
            for row in connection.execute(query)
        ]


def bounded(value, low=0, high=100):
    return max(low, min(high, value))


def calculate_scores(ticker, history):
    """Calculate all horizon scores from one historical dataset."""

    if history.empty:
        return []

    close = pd.to_numeric(
        history["Close"], errors="coerce"
    ).dropna()

    volume = pd.to_numeric(
        history["Volume"], errors="coerce"
    ).reindex(close.index).fillna(0)

    if len(close) < 200:
        return []

    price = float(close.iloc[-1])

    if not math.isfinite(price) or price <= 0:
        return []

    returns = close.pct_change().dropna()

    volatility = float(
        returns.tail(63).std() * np.sqrt(252) * 100
    )

    dollar_volume = float(
        (close * volume).tail(20).mean()
    )

    if not math.isfinite(volatility):
        return []

    if not math.isfinite(dollar_volume):
        return []

    if dollar_volume < MIN_DOLLAR_VOLUME:
        return []

    results = []

    for horizon, config in HORIZONS.items():
        momentum_days = config["momentum"]
        trend_days = config["trend"]

        if len(close) <= momentum_days:
            continue

        momentum_return = (
            price / float(close.iloc[-momentum_days - 1]) - 1
        ) * 100

        moving_average = float(
            close.tail(trend_days).mean()
        )

        trend_distance = (
            price / moving_average - 1
        ) * 100

        momentum_score = bounded(
            50 + momentum_return * 2
        )

        trend_score = bounded(
            50 + trend_distance * 2
        )

        risk_score = bounded(
            100 - volatility
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

        results.append(
            {
                "ticker": ticker,
                "horizon": horizon,
                "score": round(score, 2),
                "momentum_return": round(
                    momentum_return, 2
                ),
                "trend_distance": round(
                    trend_distance, 2
                ),
                "volatility": round(volatility, 2),
                "average_dollar_volume": round(
                    dollar_volume, 2
                ),
                "price": round(price, 4),
                "data_as_of": str(
                    close.index[-1].date()
                ),
            }
        )

    return results


def download_batch(tickers):
    """Download historical prices for a group of tickers."""

    return yf.download(
        tickers=tickers,
        period="2y",
        interval="1d",
        auto_adjust=True,
        group_by="ticker",
        threads=True,
        progress=False,
    )


def extract_history(data, ticker):
    """Extract one ticker's OHLCV data from a batch."""

    if data.empty:
        return pd.DataFrame()

    if (
        isinstance(data.columns, pd.MultiIndex)
        and ticker in data.columns.get_level_values(0)
    ):
        return data[ticker].dropna(
            subset=["Close"]
        )

    return pd.DataFrame()


def save_rankings(rows):
    if not rows:
        return

    now = datetime.now(UTC).isoformat()

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.executemany(
            """
            INSERT INTO ranking_cache (
                ticker,
                horizon,
                score,
                momentum_return,
                trend_distance,
                volatility,
                average_dollar_volume,
                price,
                data_as_of,
                calculated_at,
                methodology
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ticker, horizon, methodology)
            DO UPDATE SET
                score = excluded.score,
                momentum_return = excluded.momentum_return,
                trend_distance = excluded.trend_distance,
                volatility = excluded.volatility,
                average_dollar_volume = excluded.average_dollar_volume,
                price = excluded.price,
                data_as_of = excluded.data_as_of,
                calculated_at = excluded.calculated_at
            """,
            [
                (
                    row["ticker"],
                    row["horizon"],
                    row["score"],
                    row["momentum_return"],
                    row["trend_distance"],
                    row["volatility"],
                    row["average_dollar_volume"],
                    row["price"],
                    row["data_as_of"],
                    now,
                    METHODOLOGY,
                )
                for row in rows
            ],
        )


def run_pipeline(batch_size=40, limit=None):
    initialize_rankings()

    tickers = get_tickers(limit=limit)

    print("\n===== QUANT RANKING PIPELINE =====")
    print(f"Companies to analyze: {len(tickers)}")
    print(f"Batch size: {batch_size}")

    total_ranked = 0

    for start in range(0, len(tickers), batch_size):
        batch = tickers[start:start + batch_size]

        print(
            f"\nAnalyzing companies "
            f"{start + 1}-{start + len(batch)}..."
        )

        try:
            data = download_batch(batch)
        except Exception as exc:
            print(f"Batch download failed: {exc}")
            continue

        results = []

        for ticker in batch:
            history = extract_history(data, ticker)

            results.extend(
                calculate_scores(ticker, history)
            )

        save_rankings(results)

        total_ranked += len(
            {row["ticker"] for row in results}
        )

        print(
            f"Ranked {len(results) // 3} "
            "companies in this batch."
        )

    print("\n===== PIPELINE COMPLETE =====")
    print(f"Companies ranked: {total_ranked}")
    print(f"Total companies examined: {len(tickers)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--batch-size",
        type=int,
        default=40,
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
    )

    args = parser.parse_args()

    if args.batch_size < 1:
        parser.error("--batch-size must be positive")

    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")

    run_pipeline(
        batch_size=args.batch_size,
        limit=args.limit,
    )
