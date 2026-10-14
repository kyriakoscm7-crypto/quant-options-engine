"""Tests for historical stock-price coverage auditing."""

import pandas as pd
import pytest

from app.backtesting.universe_audit import audit_universe


def make_history(start, periods):
    dates = pd.bdate_range(start, periods=periods)

    return pd.DataFrame(
        {"Close": [100.0] * periods},
        index=dates,
    )


def test_stock_with_sufficient_history():
    histories = {
        "AAA": make_history("2023-01-01", 300),
    }

    as_of = pd.Timestamp("2024-12-31")

    result = audit_universe(
        histories,
        as_of,
        minimum_observations=252,
    )

    assert bool(result.iloc[0]["Sufficient History"])
    assert result.iloc[0]["Observations By Date"] == 300


def test_future_only_stock_has_no_prior_history():
    histories = {
        "FUTURE": make_history("2026-01-01", 100),
    }

    result = audit_universe(
        histories,
        pd.Timestamp("2024-12-31"),
    )

    assert not bool(result.iloc[0]["Has Prior Price"])
    assert result.iloc[0]["Observations By Date"] == 0


def test_short_history_is_flagged():
    histories = {
        "NEW": make_history("2024-01-01", 50),
    }

    result = audit_universe(
        histories,
        pd.Timestamp("2024-12-31"),
    )

    assert bool(result.iloc[0]["Has Prior Price"])
    assert not bool(result.iloc[0]["Sufficient History"])


def test_future_prices_are_excluded():
    histories = {
        "AAA": make_history("2024-01-01", 300),
    }

    dates = histories["AAA"].index

    result = audit_universe(
        histories,
        dates[100],
        minimum_observations=100,
    )

    assert result.iloc[0]["Observations By Date"] == 101


def test_missing_close_is_flagged():
    dates = pd.bdate_range("2024-01-01", periods=10)

    histories = {
        "BAD": pd.DataFrame(
            {"Open": [100.0] * 10},
            index=dates,
        ),
    }

    result = audit_universe(
        histories,
        pd.Timestamp("2024-12-31"),
    )

    assert not bool(result.iloc[0]["Has Prior Price"])


def test_invalid_minimum_observations():
    with pytest.raises(ValueError, match="minimum_observations"):
        audit_universe(
            {},
            pd.Timestamp("2024-01-01"),
            minimum_observations=0,
        )
