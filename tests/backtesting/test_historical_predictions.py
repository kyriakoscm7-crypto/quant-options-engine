"""Tests for historical prediction generation."""

import pandas as pd
import pytest

from app.backtesting.historical_predictions import (
    generate_historical_predictions,
)


def test_empty_calendar_raises():
    benchmark = pd.DataFrame(
        {"Close": [100.0]},
        index=pd.to_datetime(["2020-01-01"]),
    )

    with pytest.raises(ValueError, match="No benchmark trading dates"):
        generate_historical_predictions(
            histories={},
            benchmark=benchmark,
            start="2025-01-01",
            end="2025-12-31",
        )


def test_no_stocks_returns_empty_frame():
    dates = pd.bdate_range("2025-01-01", periods=30)

    benchmark = pd.DataFrame(
        {"Close": [100.0] * len(dates)},
        index=dates,
    )

    result = generate_historical_predictions(
        histories={},
        benchmark=benchmark,
        start="2025-01-01",
        end="2025-02-28",
    )

    assert result.empty
    assert "future_return" in result.columns
