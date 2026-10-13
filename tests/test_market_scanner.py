"""
Automated tests for the multi-stock market scanner.

All market-data downloads are mocked. The tests use deterministic
price series so results can be verified without internet access.
"""

from unittest.mock import patch

import pandas as pd
import pytest

from app.market_data.market_scanner import (
    MAX_SCAN_TICKERS,
    calculate_momentum,
    calculate_relative_performance,
    normalize_tickers,
    scan_market,
)


def make_history(
    prices: list[float],
    start: str = "2026-01-05",
) -> pd.DataFrame:
    """Build a deterministic daily-price history."""

    return pd.DataFrame(
        {
            "Date": pd.date_range(
                start,
                periods=len(prices),
                freq="B",
                tz="UTC",
            ),
            "Close": prices,
        }
    )


# ============================================================
# TICKER NORMALIZATION
# ============================================================


def test_normalize_comma_separated_tickers():
    assert normalize_tickers("aapl, msft, nvda") == [
        "AAPL",
        "MSFT",
        "NVDA",
    ]


def test_normalize_list_of_tickers():
    assert normalize_tickers(["aapl", "MSFT"]) == [
        "AAPL",
        "MSFT",
    ]


def test_normalize_removes_duplicates():
    assert normalize_tickers("AAPL, aapl, MSFT") == [
        "AAPL",
        "MSFT",
    ]


def test_normalize_preserves_order():
    assert normalize_tickers("NVDA, AAPL, MSFT") == [
        "NVDA",
        "AAPL",
        "MSFT",
    ]


def test_normalize_rejects_empty_string():
    with pytest.raises(ValueError):
        normalize_tickers("")


def test_normalize_rejects_empty_list():
    with pytest.raises(ValueError):
        normalize_tickers([])


def test_normalize_rejects_invalid_ticker():
    with pytest.raises(ValueError):
        normalize_tickers("AAPL, INVALID!")


def test_normalize_rejects_non_iterable():
    with pytest.raises(ValueError):
        normalize_tickers(None)


def test_normalize_rejects_too_many_tickers():
    symbols = [f"T{i}" for i in range(MAX_SCAN_TICKERS + 1)]

    with pytest.raises(ValueError):
        normalize_tickers(symbols)


def test_normalize_accepts_maximum_tickers():
    symbols = [f"T{i}" for i in range(MAX_SCAN_TICKERS)]

    assert len(normalize_tickers(symbols)) == MAX_SCAN_TICKERS


# ============================================================
# MOMENTUM
# ============================================================


def test_momentum_positive_return():
    history = make_history([100.0, 110.0, 121.0])

    assert calculate_momentum(history, 2) == 21.0


def test_momentum_negative_return():
    history = make_history([100.0, 90.0, 80.0])

    assert calculate_momentum(history, 2) == -20.0


def test_momentum_zero_return():
    history = make_history([100.0, 100.0, 100.0])

    assert calculate_momentum(history, 2) == 0.0


def test_momentum_uses_correct_lookback():
    history = make_history([100.0, 110.0, 120.0, 132.0])

    # Two-session momentum: 132 / 110 - 1 = 20%.
    assert calculate_momentum(history, 2) == 20.0


def test_momentum_insufficient_history():
    history = make_history([100.0, 110.0])

    assert calculate_momentum(history, 2) is None


def test_momentum_exact_required_history():
    history = make_history([100.0, 110.0, 120.0])

    assert calculate_momentum(history, 2) == 20.0


def test_momentum_rejects_zero_lookback():
    with pytest.raises(ValueError):
        calculate_momentum(make_history([100.0, 110.0]), 0)


def test_momentum_rejects_negative_lookback():
    with pytest.raises(ValueError):
        calculate_momentum(make_history([100.0, 110.0]), -1)


def test_momentum_rejects_boolean_lookback():
    with pytest.raises(ValueError):
        calculate_momentum(make_history([100.0, 110.0]), True)


def test_momentum_rejects_missing_close():
    with pytest.raises(ValueError):
        calculate_momentum(pd.DataFrame({"Open": [100.0]}), 1)


def test_momentum_rejects_non_dataframe():
    with pytest.raises(ValueError):
        calculate_momentum([100.0, 110.0], 1)


def test_momentum_ignores_invalid_prices():
    history = make_history([100.0, 0.0, 110.0, 121.0])

    assert calculate_momentum(history, 2) == 21.0


# ============================================================
# BENCHMARK RELATIVE PERFORMANCE
# ============================================================


def test_relative_performance_positive():
    stock = make_history([100.0, 120.0])
    benchmark = make_history([100.0, 110.0])

    assert calculate_relative_performance(stock, benchmark) == 10.0


def test_relative_performance_negative():
    stock = make_history([100.0, 90.0])
    benchmark = make_history([100.0, 110.0])

    assert calculate_relative_performance(stock, benchmark) == -20.0


def test_relative_performance_equal_returns():
    stock = make_history([100.0, 120.0])
    benchmark = make_history([200.0, 240.0])

    assert calculate_relative_performance(stock, benchmark) == 0.0


def test_relative_performance_uses_common_dates():
    stock = make_history(
        [100.0, 110.0, 121.0],
        start="2026-01-05",
    )

    benchmark = make_history(
        [200.0, 220.0, 242.0],
        start="2026-01-06",
    )

    # Shared dates: January 6 and January 7.
    # Stock: 121 / 110 - 1 = 10%.
    # Benchmark: 220 / 200 - 1 = 10%.
    assert calculate_relative_performance(stock, benchmark) == 0.0


def test_relative_performance_no_common_dates():
    stock = make_history([100.0, 110.0], start="2026-01-05")
    benchmark = make_history([100.0, 110.0], start="2026-02-02")

    assert calculate_relative_performance(stock, benchmark) is None


def test_relative_performance_one_common_date():
    stock = make_history([100.0, 110.0], start="2026-01-05")
    benchmark = make_history([200.0, 220.0], start="2026-01-06")

    assert calculate_relative_performance(stock, benchmark) is None


def test_relative_performance_rejects_missing_date():
    stock = pd.DataFrame({"Close": [100.0, 110.0]})
    benchmark = make_history([100.0, 110.0])

    with pytest.raises(ValueError):
        calculate_relative_performance(stock, benchmark)


def test_relative_performance_rejects_missing_close():
    stock = make_history([100.0, 110.0])
    benchmark = pd.DataFrame({"Date": stock["Date"]})

    with pytest.raises(ValueError):
        calculate_relative_performance(stock, benchmark)


def test_relative_performance_rejects_non_dataframe():
    with pytest.raises(ValueError):
        calculate_relative_performance(
            [100.0, 110.0],
            make_history([100.0, 110.0]),
        )


def test_relative_performance_handles_duplicate_dates():
    stock = make_history([100.0, 110.0, 120.0])
    benchmark = make_history([100.0, 105.0, 110.0])

    stock = pd.concat([stock, stock.iloc[[-1]]], ignore_index=True)

    result = calculate_relative_performance(stock, benchmark)

    expected = 20.0 - 10.0

    assert result == pytest.approx(expected)


# ============================================================
# COMPLETE MARKET SCANS
# ============================================================


@patch("app.market_data.market_scanner.fetch_stock_history")
def test_scan_multiple_stocks(mock_fetch):
    histories = {
        "SPY": make_history([100.0, 105.0, 110.0]),
        "AAPL": make_history([100.0, 110.0, 120.0]),
        "MSFT": make_history([100.0, 95.0, 90.0]),
    }

    mock_fetch.side_effect = lambda ticker, period: histories[ticker]

    result = scan_market("AAPL, MSFT", period="1y")

    assert result["Ticker"].tolist() == ["AAPL", "MSFT"]
    assert result["Status"].tolist() == ["OK", "OK"]

    assert result.loc[0, "Total Return (%)"] == 20.0
    assert result.loc[1, "Total Return (%)"] == -10.0

    assert result.loc[0, "Relative to SPY (%)"] == 10.0
    assert result.loc[1, "Relative to SPY (%)"] == -20.0


@patch("app.market_data.market_scanner.fetch_stock_history")
def test_scan_benchmark_downloaded_once(mock_fetch):
    mock_fetch.return_value = make_history([100.0, 110.0, 120.0])

    scan_market("AAPL, MSFT, NVDA")

    benchmark_calls = [
        call
        for call in mock_fetch.call_args_list
        if call.args[0] == "SPY"
    ]

    assert len(benchmark_calls) == 1


@patch("app.market_data.market_scanner.fetch_stock_history")
def test_scan_reuses_benchmark_history(mock_fetch):
    mock_fetch.return_value = make_history([100.0, 110.0, 120.0])

    result = scan_market("SPY, AAPL")

    assert result.loc[0, "Relative to SPY (%)"] == 0.0
    assert mock_fetch.call_count == 2


@patch("app.market_data.market_scanner.fetch_stock_history")
def test_scan_individual_ticker_failure(mock_fetch):
    def fake_fetch(ticker, period):
        if ticker == "MSFT":
            raise RuntimeError("Simulated provider failure")

        return make_history([100.0, 110.0, 120.0])

    mock_fetch.side_effect = fake_fetch

    result = scan_market("AAPL, MSFT, NVDA")

    assert result.loc[0, "Status"] == "OK"
    assert result.loc[1, "Status"].startswith("ERROR:")
    assert result.loc[2, "Status"] == "OK"


@patch("app.market_data.market_scanner.fetch_stock_history")
def test_scan_benchmark_failure(mock_fetch):
    def fake_fetch(ticker, period):
        if ticker == "SPY":
            raise RuntimeError("Benchmark unavailable")

        return make_history([100.0, 110.0, 120.0])

    mock_fetch.side_effect = fake_fetch

    result = scan_market("AAPL, MSFT")

    assert len(result) == 2
    assert result["Relative to SPY (%)"].isna().all()
    assert result["Status"].str.contains("benchmark unavailable").all()


@patch("app.market_data.market_scanner.fetch_stock_history")
def test_scan_invalid_ticker_does_not_download(mock_fetch):
    with pytest.raises(ValueError):
        scan_market("AAPL, INVALID!")

    mock_fetch.assert_not_called()


@patch("app.market_data.market_scanner.fetch_stock_history")
def test_scan_preserves_ticker_order(mock_fetch):
    mock_fetch.return_value = make_history([100.0, 110.0, 120.0])

    result = scan_market("NVDA, AAPL, MSFT")

    assert result["Ticker"].tolist() == ["NVDA", "AAPL", "MSFT"]


@patch("app.market_data.market_scanner.fetch_stock_history")
def test_scan_short_history_has_missing_momentum(mock_fetch):
    mock_fetch.return_value = make_history([100.0, 110.0, 120.0])

    result = scan_market("AAPL")

    assert pd.isna(result.loc[0, "1M Momentum (%)"])
    assert pd.isna(result.loc[0, "3M Momentum (%)"])
    assert result.loc[0, "Status"] == "OK"


@patch("app.market_data.market_scanner.fetch_stock_history")
def test_scan_deduplicates_tickers(mock_fetch):
    mock_fetch.return_value = make_history([100.0, 110.0, 120.0])

    result = scan_market("AAPL, aapl, MSFT")

    assert result["Ticker"].tolist() == ["AAPL", "MSFT"]