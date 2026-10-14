"""Regression tests for simulated transaction records."""

import pandas as pd
import pytest

from app.backtesting import discovery_backtest


def make_prices(values):
    dates = pd.bdate_range("2025-01-02", periods=len(values))

    history = pd.DataFrame(
        {
            "Open": values,
            "Close": values,
        },
        index=dates,
    )

    return dates, history


def test_initial_purchase_is_recorded(monkeypatch):
    dates, stock = make_prices([100.0] * 5)

    monkeypatch.setattr(
        discovery_backtest,
        "historical_rankings",
        lambda histories, as_of, horizon: pd.DataFrame(
            [{"ticker": "TEST", "score": 90.0}]
        ),
    )

    ledger = []

    result = discovery_backtest.simulate_portfolio(
        histories={"TEST": stock},
        benchmark=stock,
        rebalance_dates=[dates[0]],
        horizon="1 Year",
        config=discovery_backtest.BacktestConfig(
            initial_capital=10000.0,
            top_n=1,
            transaction_cost=0.01,
        ),
        trade_ledger=ledger,
    )

    assert len(ledger) == 1

    trade = ledger[0]

    assert trade["Ticker"] == "TEST"
    assert trade["Action"] == "BUY"
    assert trade["Execution Price"] == pytest.approx(100.0)
    assert trade["Cash Before"] == pytest.approx(10000.0)

    assert trade["Trade Value"] == pytest.approx(
        trade["Shares"] * trade["Execution Price"]
    )

    assert trade["Transaction Fee"] == pytest.approx(
        trade["Trade Value"] * 0.01
    )

    assert trade["Cash After"] == pytest.approx(
        trade["Cash Before"]
        - trade["Trade Value"]
        - trade["Transaction Fee"]
    )

    assert result["Cash"].iloc[-1] == pytest.approx(
        trade["Cash After"],
        abs=1e-6,
    )


def test_sale_is_recorded(monkeypatch):
    dates, stock = make_prices([100.0] * 8)

    other = stock.copy()

    def ranker(histories, as_of, horizon):
        ticker = "AAA" if as_of == dates[0] else "BBB"

        return pd.DataFrame(
            [{"ticker": ticker, "score": 90.0}]
        )

    ledger = []

    result = discovery_backtest.simulate_portfolio(
        histories={
            "AAA": stock,
            "BBB": other,
        },
        benchmark=stock,
        rebalance_dates=[dates[0], dates[3]],
        horizon="1 Year",
        config=discovery_backtest.BacktestConfig(
            initial_capital=10000.0,
            top_n=1,
            transaction_cost=0.01,
        ),
        ranking_function=ranker,
        trade_ledger=ledger,
    )

    actions = [
        (trade["Ticker"], trade["Action"])
        for trade in ledger
    ]

    assert actions == [
        ("AAA", "BUY"),
        ("AAA", "SELL"),
        ("BBB", "BUY"),
    ]

    sale = ledger[1]

    assert sale["Cash After"] == pytest.approx(
        sale["Cash Before"]
        + sale["Trade Value"]
        - sale["Transaction Fee"]
    )

    assert result["Cash"].iloc[-1] == pytest.approx(
        ledger[-1]["Cash After"],
        abs=1e-6,
    )


def test_ledger_does_not_change_portfolio_results(monkeypatch):
    dates, stock = make_prices(
        [100.0, 100.0, 110.0, 120.0, 130.0]
    )

    monkeypatch.setattr(
        discovery_backtest,
        "historical_rankings",
        lambda histories, as_of, horizon: pd.DataFrame(
            [{"ticker": "TEST", "score": 90.0}]
        ),
    )

    arguments = {
        "histories": {"TEST": stock},
        "benchmark": stock,
        "rebalance_dates": [dates[0]],
        "horizon": "1 Year",
        "config": discovery_backtest.BacktestConfig(
            initial_capital=10000.0,
            top_n=1,
            transaction_cost=0.001,
        ),
    }

    original = discovery_backtest.simulate_portfolio(
        **arguments
    )

    ledger = []

    instrumented = discovery_backtest.simulate_portfolio(
        **arguments,
        trade_ledger=ledger,
    )

    pd.testing.assert_frame_equal(
        original,
        instrumented,
    )

    assert len(ledger) == 1


def test_no_trade_produces_empty_ledger():
    dates, stock = make_prices([100.0] * 4)

    ledger = []

    result = discovery_backtest.simulate_portfolio(
        histories={"TEST": stock},
        benchmark=stock,
        rebalance_dates=[],
        horizon="1 Year",
        trade_ledger=ledger,
    )

    assert result.empty
    assert ledger == []
