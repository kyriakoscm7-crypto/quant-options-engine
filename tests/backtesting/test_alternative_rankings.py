"""Tests for alternative historical ranking methods."""

import pandas as pd
import pytest

from app.backtesting.alternative_rankings import (
    alternative_rankings,
    momentum_rankings,
    momentum_trend_rankings,
)


def make_history(growth):
    dates = pd.bdate_range("2024-01-01", periods=300)
    prices = [100 * (1 + growth) ** i for i in range(300)]

    return pd.DataFrame(
        {"Close": prices},
        index=dates,
    )


def test_momentum_prefers_stronger_growth():
    histories = {
        "SLOW": make_history(0.001),
        "FAST": make_history(0.003),
    }

    date = max(history.index[-1] for history in histories.values())

    result = momentum_rankings(histories, date, "1 Year")

    assert result.iloc[0]["ticker"] == "FAST"


def test_combined_ranking_returns_expected_stocks():
    histories = {
        "SLOW": make_history(0.001),
        "FAST": make_history(0.003),
    }

    date = histories["FAST"].index[-1]

    result = momentum_trend_rankings(histories, date, "1 Year")

    assert len(result) == 2
    assert result.iloc[0]["ticker"] == "FAST"


def test_future_prices_do_not_change_past_rankings():
    history = make_history(0.002)

    as_of = history.index[260]

    before = momentum_rankings(
        {"TEST": history}, as_of, "1 Year"
    )

    modified = history.copy()
    modified.loc[modified.index > as_of, "Close"] *= 100

    after = momentum_rankings(
        {"TEST": modified}, as_of, "1 Year"
    )

    pd.testing.assert_frame_equal(before, after)


def test_unknown_method_raises():
    with pytest.raises(ValueError, match="Unknown ranking method"):
        alternative_rankings(
            {},
            pd.Timestamp("2025-01-01"),
            "1 Year",
            method="invalid",
        )
