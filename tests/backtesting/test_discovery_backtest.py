"""Regression tests for Quant Discovery portfolio simulation."""

import pandas as pd

from app.backtesting import discovery_backtest


def test_missing_price_does_not_erase_existing_holding(monkeypatch):
    """A missing daily quote must not make an owned stock worth zero."""

    dates = pd.bdate_range("2025-01-02", periods=5)

    stock = pd.DataFrame(
        {
            "Open": [100.0, 100.0, 100.0, 100.0],
            "Close": [100.0, 100.0, 100.0, 100.0],
        },
        index=dates.delete(2),
    )

    benchmark = pd.DataFrame(
        {
            "Open": [100.0] * 5,
            "Close": [100.0] * 5,
        },
        index=dates,
    )

    monkeypatch.setattr(
        discovery_backtest,
        "historical_rankings",
        lambda histories, as_of, horizon: pd.DataFrame(
            [{"ticker": "TEST", "score": 90.0}]
        ),
    )

    result = discovery_backtest.simulate_portfolio(
        histories={"TEST": stock},
        benchmark=benchmark,
        rebalance_dates=[dates[0]],
        horizon="1 Year",
        config=discovery_backtest.BacktestConfig(
            initial_capital=10_000.0,
            top_n=1,
            transaction_cost=0.0,
        ),
    )

    assert len(result) == 4

    assert (
        result["Portfolio Value"]
        .between(9999.99, 10000.01)
        .all()
    )


def test_unchanged_holding_does_not_pay_repeated_trading_costs(monkeypatch):
    """Keeping an unchanged position must not trigger another trade."""

    dates = pd.bdate_range("2025-01-02", periods=8)

    stock = pd.DataFrame(
        {
            "Open": [100.0] * 8,
            "Close": [100.0] * 8,
        },
        index=dates,
    )

    benchmark = stock.copy()

    monkeypatch.setattr(
        discovery_backtest,
        "historical_rankings",
        lambda histories, as_of, horizon: pd.DataFrame(
            [{"ticker": "TEST", "score": 90.0}]
        ),
    )

    result = discovery_backtest.simulate_portfolio(
        histories={"TEST": stock},
        benchmark=benchmark,
        rebalance_dates=[dates[0], dates[3]],
        horizon="1 Year",
        config=discovery_backtest.BacktestConfig(
            initial_capital=10_000.0,
            top_n=1,
            transaction_cost=0.01,
        ),
    )

    expected_value = 10_000.0 / 1.01

    assert abs(
        result["Portfolio Value"].iloc[-1] - expected_value
    ) < 0.01


def test_stock_price_gain_increases_portfolio_value(monkeypatch):
    """A doubling stock price should double the invested portfolio."""

    dates = pd.bdate_range("2025-01-02", periods=4)

    stock = pd.DataFrame(
        {
            "Open": [100.0, 100.0, 100.0, 200.0],
            "Close": [100.0, 100.0, 100.0, 200.0],
        },
        index=dates,
    )

    benchmark = stock.copy()

    monkeypatch.setattr(
        discovery_backtest,
        "historical_rankings",
        lambda histories, as_of, horizon: pd.DataFrame(
            [{"ticker": "TEST", "score": 90.0}]
        ),
    )

    result = discovery_backtest.simulate_portfolio(
        histories={"TEST": stock},
        benchmark=benchmark,
        rebalance_dates=[dates[0]],
        horizon="1 Year",
        config=discovery_backtest.BacktestConfig(
            initial_capital=10_000.0,
            top_n=1,
            transaction_cost=0.0,
        ),
    )

    assert abs(
        result["Portfolio Value"].iloc[-1] - 20_000.0
    ) < 0.01
