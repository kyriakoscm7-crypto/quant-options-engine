"""Tests preventing future information from entering predictions."""

import pandas as pd

from app.backtesting.point_in_time import (
    create_prediction_snapshot,
    historical_news_snapshot,
    historical_price_snapshot,
)


def test_future_prices_are_excluded():
    dates = pd.date_range("2023-01-01", periods=4)

    history = pd.DataFrame(
        {"Close": [100, 110, 120, 500]},
        index=dates,
    )

    result = historical_price_snapshot(
        history,
        pd.Timestamp("2023-01-03"),
    )

    assert len(result) == 3
    assert result["Close"].iloc[-1] == 120


def test_future_news_is_excluded():
    news = pd.DataFrame(
        {
            "published_at": [
                "2023-01-01T10:00:00Z",
                "2023-01-03T10:00:00Z",
                "2023-01-05T10:00:00Z",
            ],
            "headline": [
                "Old article",
                "Available article",
                "Future article",
            ],
        }
    )

    result = historical_news_snapshot(
        news,
        pd.Timestamp("2023-01-04"),
    )

    assert len(result) == 2
    assert "Future article" not in result["headline"].tolist()


def test_prediction_snapshot_records_available_information():
    history = pd.DataFrame(
        {"Close": [100, 110, 120]},
        index=pd.date_range("2023-01-01", periods=3),
    )

    news = pd.DataFrame(
        {
            "published_at": [
                "2023-01-01T10:00:00Z",
                "2023-01-05T10:00:00Z",
            ],
        }
    )

    snapshot = create_prediction_snapshot(
        ticker="TEST",
        history=history,
        news=news,
        as_of=pd.Timestamp("2023-01-02"),
    )

    assert snapshot.latest_price_date == pd.Timestamp(
        "2023-01-02"
    )
    assert snapshot.news_count == 1


def test_future_prices_cannot_change_historical_rankings():
    """Future prices must not influence an earlier ranking."""

    from app.backtesting.discovery_backtest import historical_rankings

    dates = pd.bdate_range("2022-01-03", periods=500)

    prices = pd.Series(
        [100.0 + i * 0.1 for i in range(500)],
        index=dates,
    )

    history = pd.DataFrame(
        {
            "Open": prices,
            "High": prices * 1.01,
            "Low": prices * 0.99,
            "Close": prices,
            "Volume": [1_000_000] * 500,
        },
        index=dates,
    )

    cutoff = dates[299]

    original = historical_rankings(
        histories={"TEST": history},
        as_of=cutoff,
        horizon="1 Year",
    )

    modified_history = history.copy()

    modified_history.loc[
        modified_history.index > cutoff,
        "Close",
    ] = 1_000_000.0

    modified = historical_rankings(
        histories={"TEST": modified_history},
        as_of=cutoff,
        horizon="1 Year",
    )

    assert not original.empty, (
        "Test requires an eligible historical ranking."
    )

    pd.testing.assert_frame_equal(original, modified)
