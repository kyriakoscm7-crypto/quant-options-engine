"""
Quant Intelligence — Portfolio Risk Analytics Tests.

Tests historical portfolio valuation, returns, risk statistics,
benchmark sensitivity, diversification, and invalid inputs.

All prices are synthetic. No internet connection is required.
"""

import math

import numpy as np
import pandas as pd
import pytest

from app.portfolio.portfolio_analytics import (
    analyze_portfolio_risk,
    calculate_annualized_return,
    calculate_annualized_volatility,
    calculate_asset_correlations,
    calculate_daily_returns,
    calculate_diversification_ratio,
    calculate_maximum_drawdown,
    calculate_portfolio_beta,
    calculate_portfolio_values,
    calculate_risk_contributions,
    calculate_sharpe_ratio,
    validate_price_history,
)
from app.portfolio.portfolio_manager import StockHolding, StockPortfolio

# ============================================================
# TEST DATA
# ============================================================


@pytest.fixture
def dates():
    """Create five consecutive business dates."""
    return pd.date_range("2026-01-05", periods=5, freq="B")


@pytest.fixture
def portfolio():
    """Create a two-stock portfolio with fixed share quantities."""
    return StockPortfolio(
        [
            StockHolding("AAPL", 10, 100),
            StockHolding("MSFT", 5, 200),
        ]
    )


@pytest.fixture
def prices(dates):
    """Create deterministic historical stock prices."""
    return pd.DataFrame(
        {
            "AAPL": [100, 110, 105, 115, 120],
            "MSFT": [200, 210, 190, 220, 230],
        },
        index=dates,
    )


@pytest.fixture
def portfolio_values(dates):
    """Known portfolio values for the synthetic test data."""
    return pd.Series(
        [2000, 2150, 2000, 2250, 2350],
        index=dates,
        name="Portfolio Value",
    )


@pytest.fixture
def daily_returns(portfolio_values):
    """Calculate the known portfolio return series."""
    return portfolio_values.pct_change(fill_method=None).dropna()


# ============================================================
# HISTORICAL PRICE VALIDATION
# ============================================================


def test_validate_price_history(prices):
    result = validate_price_history(prices, ["AAPL", "MSFT"])

    assert isinstance(result, pd.DataFrame)
    assert result.shape == (5, 2)


def test_validate_price_history_sorts_dates(prices):
    shuffled = prices.iloc[::-1]

    result = validate_price_history(shuffled, ["AAPL", "MSFT"])

    assert result.index.is_monotonic_increasing


def test_validate_price_history_preserves_ticker_order(prices):
    result = validate_price_history(prices, ["MSFT", "AAPL"])

    assert list(result.columns) == ["MSFT", "AAPL"]


def test_validate_price_history_rejects_missing_ticker(prices):
    with pytest.raises(ValueError):
        validate_price_history(prices, ["AAPL", "NVDA"])


def test_validate_price_history_rejects_empty_dataframe():
    with pytest.raises(ValueError):
        validate_price_history(pd.DataFrame(), ["AAPL"])


def test_validate_price_history_rejects_non_dataframe():
    with pytest.raises(TypeError):
        validate_price_history([100, 110, 120], ["AAPL"])


def test_validate_price_history_rejects_non_datetime_index():
    invalid = pd.DataFrame({"AAPL": [100, 110, 120]})

    with pytest.raises(ValueError):
        validate_price_history(invalid, ["AAPL"])


def test_validate_price_history_rejects_duplicate_dates(prices):
    invalid = prices.copy()

    invalid.index = [
        prices.index[0],
        prices.index[0],
        prices.index[2],
        prices.index[3],
        prices.index[4],
    ]

    with pytest.raises(ValueError):
        validate_price_history(invalid, ["AAPL", "MSFT"])


def test_validate_price_history_rejects_duplicate_columns(prices):
    invalid = prices.copy()
    invalid.columns = ["AAPL", "AAPL"]

    with pytest.raises(ValueError):
        validate_price_history(invalid, ["AAPL"])


@pytest.mark.parametrize("invalid_price", [0, -1, -100, np.inf, -np.inf])
def test_validate_price_history_rejects_invalid_prices(
    prices,
    invalid_price,
):
    # Convert to float so pandas accepts infinity as test data.
    invalid = prices.astype(float).copy()
    invalid.loc[invalid.index[0], "AAPL"] = invalid_price

    with pytest.raises(ValueError):
        validate_price_history(invalid, ["AAPL", "MSFT"])


def test_validate_price_history_removes_missing_dates(prices):
    modified = prices.copy()
    modified.loc[modified.index[2], "AAPL"] = np.nan

    result = validate_price_history(modified, ["AAPL", "MSFT"])

    assert len(result) == 4
    assert modified.index[2] not in result.index


def test_validate_price_history_rejects_insufficient_data(prices):
    with pytest.raises(ValueError):
        validate_price_history(prices.iloc[:2], ["AAPL", "MSFT"])


# ============================================================
# PORTFOLIO VALUATION
# ============================================================


def test_calculate_portfolio_values(portfolio, prices):
    result = calculate_portfolio_values(portfolio, prices)

    expected = np.array([2000, 2150, 2000, 2250, 2350])

    np.testing.assert_allclose(result.to_numpy(), expected)


def test_portfolio_values_preserve_dates(portfolio, prices):
    result = calculate_portfolio_values(portfolio, prices)

    pd.testing.assert_index_equal(result.index, prices.index)


def test_portfolio_values_reject_empty_portfolio(prices):
    empty = StockPortfolio([])

    with pytest.raises(ValueError):
        calculate_portfolio_values(empty, prices)


def test_portfolio_values_reject_zero_share_portfolio(prices):
    zero = StockPortfolio(
        [
            StockHolding("AAPL", 0, 100),
            StockHolding("MSFT", 0, 200),
        ]
    )

    with pytest.raises(ValueError):
        calculate_portfolio_values(zero, prices)


def test_portfolio_values_reject_invalid_portfolio(prices):
    with pytest.raises(TypeError):
        calculate_portfolio_values("not a portfolio", prices)


def test_portfolio_values_ignore_stored_purchase_prices(prices):
    """Historical values must depend on shares and historical prices."""
    portfolio = StockPortfolio(
        [
            StockHolding("AAPL", 10, 999),
            StockHolding("MSFT", 5, 999),
        ]
    )

    result = calculate_portfolio_values(portfolio, prices)

    assert result.iloc[0] == pytest.approx(2000)
    assert result.iloc[-1] == pytest.approx(2350)


# ============================================================
# DAILY RETURNS
# ============================================================


def test_calculate_daily_returns(portfolio_values):
    result = calculate_daily_returns(portfolio_values)

    expected = np.array(
        [
            2150 / 2000 - 1,
            2000 / 2150 - 1,
            2250 / 2000 - 1,
            2350 / 2250 - 1,
        ]
    )

    np.testing.assert_allclose(result.to_numpy(), expected)


def test_daily_returns_observation_count(portfolio_values):
    result = calculate_daily_returns(portfolio_values)

    assert len(result) == 4


def test_daily_returns_reject_insufficient_data(dates):
    values = pd.Series([100, 110], index=dates[:2])

    with pytest.raises(ValueError):
        calculate_daily_returns(values)


@pytest.mark.parametrize("invalid_value", [0, -100, np.nan, np.inf])
def test_daily_returns_reject_invalid_values(
    portfolio_values,
    invalid_value,
):
    # Use float values to test NaN and infinity safely.
    values = portfolio_values.astype(float).copy()
    values.iloc[1] = invalid_value

    with pytest.raises(ValueError):
        calculate_daily_returns(values)


# ============================================================
# MAXIMUM DRAWDOWN
# ============================================================


def test_maximum_drawdown(portfolio_values):
    result = calculate_maximum_drawdown(portfolio_values)

    expected = (2000 / 2150 - 1) * 100

    assert result == pytest.approx(expected)


def test_maximum_drawdown_for_increasing_values(dates):
    values = pd.Series([100, 110, 120, 130, 140], index=dates)

    assert calculate_maximum_drawdown(values) == pytest.approx(0)


def test_maximum_drawdown_for_declining_values(dates):
    values = pd.Series([100, 90, 80, 70, 60], index=dates)

    assert calculate_maximum_drawdown(values) == pytest.approx(-40)


def test_maximum_drawdown_rejects_empty_series():
    with pytest.raises(ValueError):
        calculate_maximum_drawdown(pd.Series(dtype=float))


# ============================================================
# ANNUALIZED RETURN
# ============================================================


def test_annualized_return(portfolio_values):
    expected = ((2350 / 2000) ** (252 / 4) - 1) * 100

    result = calculate_annualized_return(portfolio_values)

    assert result == pytest.approx(expected)


def test_annualized_return_for_flat_portfolio(dates):
    values = pd.Series([100, 100, 100, 100, 100], index=dates)

    assert calculate_annualized_return(values) == pytest.approx(0)


def test_annualized_return_custom_trading_days(dates):
    values = pd.Series([100, 110, 120, 130, 140], index=dates)

    expected = ((140 / 100) ** (100 / 4) - 1) * 100

    result = calculate_annualized_return(
        values,
        trading_days_per_year=100,
    )

    assert result == pytest.approx(expected)


def test_annualized_return_rejects_invalid_trading_days(portfolio_values):
    with pytest.raises(ValueError):
        calculate_annualized_return(
            portfolio_values,
            trading_days_per_year=0,
        )


# ============================================================
# ANNUALIZED VOLATILITY
# ============================================================


def test_annualized_volatility(daily_returns):
    expected = (
        np.std(daily_returns.to_numpy(), ddof=1)
        * math.sqrt(252)
        * 100
    )

    result = calculate_annualized_volatility(daily_returns)

    assert result == pytest.approx(expected)


def test_annualized_volatility_zero_for_constant_returns(dates):
    returns = pd.Series([0.01, 0.01, 0.01, 0.01], index=dates[:4])

    result = calculate_annualized_volatility(returns)

    assert result == pytest.approx(0, abs=1e-10)


def test_annualized_volatility_custom_trading_days(daily_returns):
    expected = (
        np.std(daily_returns.to_numpy(), ddof=1)
        * math.sqrt(100)
        * 100
    )

    result = calculate_annualized_volatility(
        daily_returns,
        trading_days_per_year=100,
    )

    assert result == pytest.approx(expected)


# ============================================================
# SHARPE RATIO
# ============================================================


def test_sharpe_ratio(daily_returns):
    expected = (
        daily_returns.mean()
        / daily_returns.std(ddof=1)
        * math.sqrt(252)
    )

    result = calculate_sharpe_ratio(daily_returns)

    assert result == pytest.approx(expected)


def test_sharpe_ratio_with_risk_free_rate(daily_returns):
    annual_rate = 0.04

    daily_rate = (1 + annual_rate) ** (1 / 252) - 1

    expected = (
        (daily_returns - daily_rate).mean()
        / daily_returns.std(ddof=1)
        * math.sqrt(252)
    )

    result = calculate_sharpe_ratio(
        daily_returns,
        annual_risk_free_rate=annual_rate,
    )

    assert result == pytest.approx(expected)


def test_sharpe_ratio_rejects_invalid_risk_free_rate(daily_returns):
    with pytest.raises(ValueError):
        calculate_sharpe_ratio(
            daily_returns,
            annual_risk_free_rate=-1,
        )


def test_sharpe_ratio_returns_none_for_zero_volatility(dates):
    returns = pd.Series([0, 0, 0, 0], index=dates[:4])

    assert calculate_sharpe_ratio(returns) is None


# ============================================================
# CORRELATION MATRIX
# ============================================================


def test_asset_correlations(prices):
    correlations = calculate_asset_correlations(prices)

    assert correlations.shape == (2, 2)
    assert correlations.loc["AAPL", "AAPL"] == pytest.approx(1)
    assert correlations.loc["MSFT", "MSFT"] == pytest.approx(1)


def test_asset_correlations_are_symmetric(prices):
    correlations = calculate_asset_correlations(prices)

    np.testing.assert_allclose(
        correlations.to_numpy(),
        correlations.to_numpy().T,
    )


def test_perfect_positive_correlation(dates):
    prices = pd.DataFrame(
        {
            "AAPL": [100, 110, 100, 120, 110],
            "MSFT": [200, 220, 200, 240, 220],
        },
        index=dates,
    )

    correlations = calculate_asset_correlations(prices)

    assert correlations.loc["AAPL", "MSFT"] == pytest.approx(1)


# ============================================================
# PORTFOLIO BETA
# ============================================================


def test_portfolio_beta(dates):
    benchmark_prices = pd.Series(
        [100, 110, 99, 108.9, 98.01],
        index=dates,
    )

    benchmark_returns = benchmark_prices.pct_change().dropna()

    portfolio_returns = benchmark_returns * 2

    result = calculate_portfolio_beta(
        portfolio_returns,
        benchmark_prices,
    )

    assert result == pytest.approx(2)


def test_portfolio_beta_returns_none_for_flat_benchmark(dates):
    benchmark_prices = pd.Series(
        [100, 100, 100, 100, 100],
        index=dates,
    )

    portfolio_returns = pd.Series(
        [0.01, -0.02, 0.03, -0.01],
        index=dates[1:],
    )

    assert (
        calculate_portfolio_beta(
            portfolio_returns,
            benchmark_prices,
        )
        is None
    )


def test_portfolio_beta_rejects_insufficient_overlap(dates):
    benchmark_prices = pd.Series(
        [100, 110, 120],
        index=dates[:3],
    )

    portfolio_returns = pd.Series(
        [0.01, 0.02],
        index=dates[3:],
    )

    with pytest.raises(ValueError):
        calculate_portfolio_beta(
            portfolio_returns,
            benchmark_prices,
        )


# ============================================================
# RISK CONTRIBUTIONS
# ============================================================


def test_risk_contributions(portfolio, prices):
    result = calculate_risk_contributions(portfolio, prices)

    assert len(result) == 2
    assert list(result["Ticker"]) == ["AAPL", "MSFT"]


def test_risk_contributions_sum_to_100(portfolio, prices):
    result = calculate_risk_contributions(portfolio, prices)

    assert result["Risk Contribution (%)"].sum() == pytest.approx(100)


def test_risk_contributions_use_final_historical_weights(prices):
    """
    Stored holding prices deliberately differ from the final
    historical prices to detect incorrect weight calculations.
    """
    portfolio = StockPortfolio(
        [
            StockHolding("AAPL", 10, 1000),
            StockHolding("MSFT", 5, 1),
        ]
    )

    result = calculate_risk_contributions(portfolio, prices)

    expected_aapl_weight = 1200 / 2350 * 100
    expected_msft_weight = 1150 / 2350 * 100

    assert result.loc[0, "Weight (%)"] == pytest.approx(
        expected_aapl_weight
    )

    assert result.loc[1, "Weight (%)"] == pytest.approx(
        expected_msft_weight
    )


def test_risk_contributions_match_independent_covariance(prices):
    portfolio = StockPortfolio(
        [
            StockHolding("AAPL", 10, 999),
            StockHolding("MSFT", 5, 999),
        ]
    )

    result = calculate_risk_contributions(portfolio, prices)

    returns = prices.pct_change(fill_method=None).dropna()
    covariance = returns.cov().to_numpy()

    weights = np.array([1200 / 2350, 1150 / 2350])

    variance = weights @ covariance @ weights

    expected_contributions = (
        weights * (covariance @ weights) / variance * 100
    )

    np.testing.assert_allclose(
        result["Risk Contribution (%)"].to_numpy(),
        expected_contributions,
    )


# ============================================================
# DIVERSIFICATION RATIO
# ============================================================


def test_diversification_ratio(portfolio, prices):
    result = calculate_diversification_ratio(portfolio, prices)

    assert result is not None
    assert result >= 1


def test_diversification_ratio_matches_independent_formula(prices):
    portfolio = StockPortfolio(
        [
            StockHolding("AAPL", 10, 999),
            StockHolding("MSFT", 5, 999),
        ]
    )

    result = calculate_diversification_ratio(portfolio, prices)

    returns = prices.pct_change(fill_method=None).dropna()
    covariance = returns.cov().to_numpy()

    weights = np.array([1200 / 2350, 1150 / 2350])

    individual_volatilities = np.sqrt(np.diag(covariance))
    portfolio_volatility = np.sqrt(weights @ covariance @ weights)

    expected = (
        weights @ individual_volatilities
    ) / portfolio_volatility

    assert result == pytest.approx(expected)


def test_diversification_ratio_single_stock(dates):
    portfolio = StockPortfolio(
        [StockHolding("AAPL", 10, 100)]
    )

    prices = pd.DataFrame(
        {"AAPL": [100, 110, 105, 115, 120]},
        index=dates,
    )

    result = calculate_diversification_ratio(portfolio, prices)

    assert result == pytest.approx(1)


# ============================================================
# COMPLETE PORTFOLIO RISK ANALYSIS
# ============================================================


def test_analyze_portfolio_risk(portfolio, prices):
    summary = analyze_portfolio_risk(portfolio, prices)

    assert summary.initial_value == pytest.approx(2000)
    assert summary.final_value == pytest.approx(2350)
    assert summary.total_return_pct == pytest.approx(17.5)


def test_analyze_portfolio_risk_observation_count(portfolio, prices):
    summary = analyze_portfolio_risk(portfolio, prices)

    assert summary.observation_count == 4


def test_analyze_portfolio_risk_dates(portfolio, prices):
    summary = analyze_portfolio_risk(portfolio, prices)

    assert summary.start_date == prices.index[0]
    assert summary.end_date == prices.index[-1]


def test_analyze_portfolio_risk_drawdown(portfolio, prices):
    summary = analyze_portfolio_risk(portfolio, prices)

    expected = (2000 / 2150 - 1) * 100

    assert summary.maximum_drawdown_pct == pytest.approx(expected)


def test_analyze_portfolio_risk_without_benchmark(portfolio, prices):
    summary = analyze_portfolio_risk(portfolio, prices)

    assert summary.beta is None


def test_analyze_portfolio_risk_with_benchmark(portfolio, prices):
    benchmark_prices = pd.Series(
        [100, 105, 102, 108, 112],
        index=prices.index,
    )

    summary = analyze_portfolio_risk(
        portfolio,
        prices,
        benchmark_prices=benchmark_prices,
    )

    assert summary.beta is not None
    assert math.isfinite(summary.beta)


def test_analyze_portfolio_risk_sharpe(portfolio, prices):
    summary = analyze_portfolio_risk(
        portfolio,
        prices,
        annual_risk_free_rate=0.04,
    )

    assert summary.sharpe_ratio is not None
    assert math.isfinite(summary.sharpe_ratio)


# ============================================================
# PORTFOLIO BETA — RELIABILITY AND DATA VALIDATION
# ============================================================


@pytest.mark.parametrize(
    "invalid_price",
    [0.0, -100.0, np.inf, -np.inf],
)
def test_portfolio_beta_rejects_invalid_benchmark_prices(
    dates,
    invalid_price,
):
    """Reject benchmark prices that cannot represent valid asset prices."""

    benchmark_prices = pd.Series(
        [100.0, 105.0, 110.0, 115.0, 120.0],
        index=dates,
    )

    benchmark_prices.iloc[2] = invalid_price

    portfolio_returns = pd.Series(
        [0.01, 0.02, -0.01, 0.03],
        index=dates[1:],
    )

    with pytest.raises(ValueError):
        calculate_portfolio_beta(
            portfolio_returns,
            benchmark_prices,
        )


def test_portfolio_beta_rejects_duplicate_benchmark_dates(dates):
    """Duplicate dates must not create ambiguous benchmark returns."""

    benchmark_prices = pd.Series(
        [100.0, 105.0, 110.0, 115.0, 120.0],
        index=[
            dates[0],
            dates[1],
            dates[1],
            dates[3],
            dates[4],
        ],
    )

    portfolio_returns = pd.Series(
        [0.01, 0.02, -0.01, 0.03],
        index=dates[1:],
    )

    with pytest.raises(ValueError):
        calculate_portfolio_beta(
            portfolio_returns,
            benchmark_prices,
        )


def test_portfolio_beta_rejects_non_datetime_benchmark_index():
    """Benchmark observations must be associated with trading dates."""

    benchmark_prices = pd.Series(
        [100.0, 105.0, 110.0, 115.0, 120.0],
    )

    portfolio_returns = pd.Series(
        [0.01, 0.02, -0.01, 0.03],
    )

    with pytest.raises(ValueError):
        calculate_portfolio_beta(
            portfolio_returns,
            benchmark_prices,
        )


def test_portfolio_beta_rejects_infinite_portfolio_returns(dates):
    """Infinite portfolio returns must never enter covariance calculations."""

    benchmark_prices = pd.Series(
        [100.0, 105.0, 110.0, 115.0, 120.0],
        index=dates,
    )

    portfolio_returns = pd.Series(
        [0.01, np.inf, -0.01, 0.03],
        index=dates[1:],
    )

    with pytest.raises(ValueError):
        calculate_portfolio_beta(
            portfolio_returns,
            benchmark_prices,
        )


def test_portfolio_beta_rejects_duplicate_portfolio_dates(dates):
    """Duplicate portfolio return dates must be rejected."""

    benchmark_prices = pd.Series(
        [100.0, 105.0, 110.0, 115.0, 120.0],
        index=dates,
    )

    portfolio_returns = pd.Series(
        [0.01, 0.02, -0.01, 0.03],
        index=[
            dates[1],
            dates[1],
            dates[3],
            dates[4],
        ],
    )

    with pytest.raises(ValueError):
        calculate_portfolio_beta(
            portfolio_returns,
            benchmark_prices,
        )


def test_portfolio_beta_handles_missing_benchmark_prices(dates):
    """
    Missing benchmark prices must not be forward-filled.

    Returns involving the missing observation are excluded.
    """

    benchmark_prices = pd.Series(
        [100.0, 105.0, np.nan, 115.0, 120.0],
        index=dates,
    )

    portfolio_returns = pd.Series(
        [0.01, 0.02, -0.01, 0.03],
        index=dates[1:],
    )

    # Only two benchmark returns remain valid:
    # dates[1] and dates[4].
    result = calculate_portfolio_beta(
        portfolio_returns,
        benchmark_prices,
    )

    assert result is not None
    assert np.isfinite(result)