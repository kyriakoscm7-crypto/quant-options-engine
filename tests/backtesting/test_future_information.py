"""Tests preventing future price information from influencing decisions."""

import pandas as pd

from app.backtesting.alternative_rankings import (
    momentum_trend_rankings,
)
from app.backtesting.discovery_backtest import (
    BacktestConfig,
    simulate_portfolio,
)


def make_history(growth, periods=350):
    dates = pd.bdate_range("2024-01-01", periods=periods)

    prices = [
        100.0 * (1.0 + growth) ** index
        for index in range(periods)
    ]

    return pd.DataFrame(
        {
            "Open": prices,
            "Close": prices,
        },
        index=dates,
    )


def test_future_prices_cannot_change_past_rankings():
    histories = {
        "FAST": make_history(0.003),
        "SLOW": make_history(0.001),
        "MEDIUM": make_history(0.002),
    }

    as_of = histories["FAST"].index[270]

    original = momentum_trend_rankings(
        histories,
        as_of,
        "1 Year",
    )

    modified = {
        ticker: history.copy()
        for ticker, history in histories.items()
    }

    for ticker, history in modified.items():
        future = history.index > as_of

        multiplier = 1000.0 if ticker == "SLOW" else 0.001

        history.loc[future, ["Open", "Close"]] *= multiplier

    after = momentum_trend_rankings(
        modified,
        as_of,
        "1 Year",
    )

    pd.testing.assert_frame_equal(
        original,
        after,
        check_exact=True,
    )


def test_future_only_company_is_not_selected():
    existing = make_history(0.002)

    as_of = existing.index[270]

    future_dates = pd.bdate_range(
        as_of + pd.Timedelta(days=1),
        periods=50,
    )

    future_company = pd.DataFrame(
        {
            "Open": [100.0 * 1.5**i for i in range(50)],
            "Close": [100.0 * 1.5**i for i in range(50)],
        },
        index=future_dates,
    )

    rankings = momentum_trend_rankings(
        {
            "EXISTING": existing,
            "FUTURE": future_company,
        },
        as_of,
        "1 Year",
    )

    assert "FUTURE" not in rankings["ticker"].tolist()


def test_simulator_executes_after_ranking_date():
    history = make_history(0.001)

    as_of = history.index[270]

    ledger = []

    simulate_portfolio(
        histories={"TEST": history},
        benchmark=history,
        rebalance_dates=[as_of],
        horizon="1 Year",
        config=BacktestConfig(
            initial_capital=10000.0,
            top_n=1,
            transaction_cost=0.001,
        ),
        ranking_function=momentum_trend_rankings,
        trade_ledger=ledger,
    )

    assert ledger, "Expected at least one trade."

    assert all(
        pd.Timestamp(trade["Date"]) > as_of
        for trade in ledger
    )
