"""Point-in-time data controls for historical strategy research."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class PredictionSnapshot:
    """Metadata describing the information available for a prediction."""

    as_of: pd.Timestamp
    ticker: str
    latest_price_date: pd.Timestamp | None
    news_count: int


def historical_price_snapshot(
    history: pd.DataFrame,
    as_of: pd.Timestamp,
) -> pd.DataFrame:
    """Return only price observations available by the cutoff."""

    cutoff = pd.Timestamp(as_of)

    if history.empty:
        return history.copy()

    if not isinstance(history.index, pd.DatetimeIndex):
        raise TypeError("Price history must have a DatetimeIndex.")

    return history.loc[history.index <= cutoff].copy()


def historical_news_snapshot(
    news: pd.DataFrame,
    as_of: pd.Timestamp,
    published_column: str = "published_at",
) -> pd.DataFrame:
    """Return only news published by the cutoff."""

    if news.empty:
        return news.copy()

    if published_column not in news.columns:
        raise ValueError(
            f"News data requires '{published_column}'."
        )

    cutoff = pd.Timestamp(as_of)

    publication_times = pd.to_datetime(
        news[published_column],
        utc=True,
        errors="coerce",
    )

    if cutoff.tzinfo is None:
        cutoff = cutoff.tz_localize("UTC")
    else:
        cutoff = cutoff.tz_convert("UTC")

    eligible = publication_times.notna() & (
        publication_times <= cutoff
    )

    return news.loc[eligible].copy()


def create_prediction_snapshot(
    ticker: str,
    history: pd.DataFrame,
    news: pd.DataFrame,
    as_of: pd.Timestamp,
) -> PredictionSnapshot:
    """Record the latest data available when a prediction was made."""

    prices = historical_price_snapshot(history, as_of)
    articles = historical_news_snapshot(news, as_of)

    latest_price_date = (
        pd.Timestamp(prices.index[-1])
        if not prices.empty
        else None
    )

    return PredictionSnapshot(
        as_of=pd.Timestamp(as_of),
        ticker=ticker,
        latest_price_date=latest_price_date,
        news_count=len(articles),
    )
