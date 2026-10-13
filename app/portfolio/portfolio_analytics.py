"""
Quant Intelligence — Portfolio Risk Analytics.

Historical portfolio analytics for long-only stock portfolios.

Features:
- Date-aligned historical price analysis.
- Fixed-share portfolio valuation.
- Daily portfolio returns.
- Annualized return and volatility.
- Sharpe ratio.
- Maximum drawdown.
- Benchmark beta.
- Asset correlation and covariance.
- Portfolio variance contributions.
- Diversification ratio.

Important assumptions:
- Share quantities remain constant throughout history.
- No deposits, withdrawals, or rebalancing.
- No transaction costs or taxes.
- Prices must be consistently adjusted for corporate actions.
- Historical results are descriptive, not predictive.

This module does not download market data. It operates on
supplied price DataFrames, making it independently testable.
"""

from dataclasses import dataclass
from math import isfinite, sqrt

import numpy as np
import pandas as pd

from app.portfolio.portfolio_manager import StockPortfolio

TRADING_DAYS_PER_YEAR = 252
MINIMUM_RETURN_OBSERVATIONS = 2


@dataclass(frozen=True)
class PortfolioRiskSummary:
    """
    Structured historical portfolio risk statistics.

    Returns and volatility are expressed as percentages.
    Beta, Sharpe ratio, and diversification ratio are
    dimensionless.
    """

    observation_count: int
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    initial_value: float
    final_value: float
    total_return_pct: float
    annualized_return_pct: float
    annualized_volatility_pct: float
    sharpe_ratio: float | None
    maximum_drawdown_pct: float
    beta: float | None
    diversification_ratio: float | None


def validate_price_history(
    prices: pd.DataFrame,
    required_tickers: list[str],
) -> pd.DataFrame:
    """
    Validate historical prices and return aligned observations.

    Expected input:
        Index: trading dates
        Columns: stock tickers
        Values: positive, finite prices

    Missing dates are removed using a common-date intersection.
    Prices are never forward-filled because doing so could
    artificially suppress measured volatility.
    """

    if not isinstance(prices, pd.DataFrame):
        raise TypeError("prices must be a pandas DataFrame.")

    if prices.empty:
        raise ValueError("Historical price data cannot be empty.")

    if not isinstance(prices.index, pd.DatetimeIndex):
        raise ValueError(
            "Historical prices must use a DatetimeIndex."
        )

    if prices.index.has_duplicates:
        raise ValueError(
            "Historical prices contain duplicate dates."
        )

    if prices.columns.has_duplicates:
        raise ValueError(
            "Historical prices contain duplicate ticker columns."
        )

    missing_tickers = [
        ticker
        for ticker in required_tickers
        if ticker not in prices.columns
    ]

    if missing_tickers:
        raise ValueError(
            "Missing historical prices for: "
            + ", ".join(missing_tickers)
        )

    selected = prices.loc[:, required_tickers].copy()

    for ticker in required_tickers:
        try:
            selected[ticker] = pd.to_numeric(
                selected[ticker],
                errors="raise",
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Invalid historical prices for {ticker}."
            ) from exc

    selected = selected.sort_index()

    # Reject infinite prices before removing missing observations.
    # Depending on pandas configuration, infinity can otherwise
    # be interpreted as missing data and silently discarded.
    numeric_values = selected.to_numpy(dtype=float)

    if np.isinf(numeric_values).any():
        raise ValueError(
            "Historical prices cannot contain infinite values."
        )

    # Missing observations are excluded rather than filled.
    selected = selected.dropna(how="any")

    if len(selected) < MINIMUM_RETURN_OBSERVATIONS + 1:
        raise ValueError(
            "At least three common price observations "
            "are required."
        )

    values = selected.to_numpy(dtype=float)

    if not np.isfinite(values).all():
        raise ValueError(
            "Historical prices must contain finite values."
        )

    if (values <= 0).any():
        raise ValueError(
            "Historical prices must be strictly positive."
        )

    return selected.astype(float)


def calculate_portfolio_values(
    portfolio: StockPortfolio,
    prices: pd.DataFrame,
) -> pd.Series:
    """
    Calculate fixed-share historical portfolio values.

    Portfolio Value(t) = sum(Shares_i × Price_i(t))

    Share quantities are fixed, but allocation percentages
    change naturally as stock prices change.
    """

    if not isinstance(portfolio, StockPortfolio):
        raise TypeError(
            "portfolio must be a StockPortfolio instance."
        )

    if portfolio.holding_count == 0:
        raise ValueError(
            "Cannot analyze an empty portfolio."
        )

    tickers = [
        holding.ticker
        for holding in portfolio.holdings
    ]

    aligned = validate_price_history(
        prices,
        tickers,
    )

    quantities = np.array(
        [
            holding.shares
            for holding in portfolio.holdings
        ],
        dtype=float,
    )

    if quantities.sum() <= 0:
        raise ValueError(
            "Portfolio must contain positive share quantities."
        )

    values = aligned.to_numpy() @ quantities

    if not np.isfinite(values).all():
        raise ValueError(
            "Calculated portfolio values are not finite."
        )

    result = pd.Series(
        values,
        index=aligned.index,
        name="Portfolio Value",
    )

    return result


def calculate_daily_returns(
    portfolio_values: pd.Series,
) -> pd.Series:
    """
    Calculate simple daily portfolio returns.

    Return(t) = Value(t) / Value(t-1) - 1
    """

    if not isinstance(portfolio_values, pd.Series):
        raise TypeError(
            "portfolio_values must be a pandas Series."
        )

    if len(portfolio_values) < 3:
        raise ValueError(
            "At least three portfolio values are required."
        )

    values = pd.to_numeric(
        portfolio_values,
        errors="raise",
    ).astype(float)

    # Reject infinity explicitly before any return calculation.
    if np.isinf(values.to_numpy(dtype=float)).any():
        raise ValueError(
            "Portfolio values cannot contain infinite values."
        )

    if not np.isfinite(values.to_numpy()).all():
        raise ValueError(
            "Portfolio values must be finite."
        )

    if (values <= 0).any():
        raise ValueError(
            "Portfolio values must be positive."
        )

    returns = values.pct_change(
        fill_method=None
    ).dropna()

    returns.name = "Portfolio Return"

    return returns


def calculate_maximum_drawdown(
    portfolio_values: pd.Series,
) -> float:
    """
    Calculate maximum historical drawdown as a percentage.

    Drawdown(t) = Value(t) / RunningPeak(t) - 1

    The result is zero or negative.
    """

    if portfolio_values.empty:
        raise ValueError(
            "Portfolio values cannot be empty."
        )

    running_peak = portfolio_values.cummax()

    drawdowns = (
        portfolio_values / running_peak - 1
    )

    return float(
        drawdowns.min() * 100
    )


def calculate_annualized_return(
    portfolio_values: pd.Series,
    trading_days_per_year: int = TRADING_DAYS_PER_YEAR,
) -> float:
    """
    Calculate compounded annualized historical return.

    Annualized Return =
        (Final Value / Initial Value) ** (252 / N) - 1

    N is the number of daily return intervals.
    """

    if trading_days_per_year <= 0:
        raise ValueError(
            "trading_days_per_year must be positive."
        )

    if len(portfolio_values) < 2:
        raise ValueError(
            "At least two portfolio values are required."
        )

    initial = float(portfolio_values.iloc[0])
    final = float(portfolio_values.iloc[-1])

    if initial <= 0 or final <= 0:
        raise ValueError(
            "Portfolio values must be positive."
        )

    intervals = len(portfolio_values) - 1

    annualized = (
        (final / initial)
        ** (trading_days_per_year / intervals)
        - 1
    )

    return float(
        annualized * 100
    )


def calculate_annualized_volatility(
    daily_returns: pd.Series,
    trading_days_per_year: int = TRADING_DAYS_PER_YEAR,
) -> float:
    """
    Calculate annualized sample standard deviation.

    Annualized Volatility =
        std(daily returns, ddof=1) × sqrt(252)
    """

    if len(daily_returns) < 2:
        raise ValueError(
            "At least two daily returns are required."
        )

    if trading_days_per_year <= 0:
        raise ValueError(
            "trading_days_per_year must be positive."
        )

    daily_volatility = float(
        daily_returns.std(ddof=1)
    )

    return (
        daily_volatility
        * sqrt(trading_days_per_year)
        * 100
    )


def calculate_sharpe_ratio(
    daily_returns: pd.Series,
    annual_risk_free_rate: float = 0.0,
    trading_days_per_year: int = TRADING_DAYS_PER_YEAR,
) -> float | None:
    """
    Calculate an annualized historical Sharpe ratio.

    Risk-free rate is supplied as a decimal:
        0.04 means 4% annually.

    Uses a constant daily risk-free rate derived from
    the annual rate.

    Returns None when portfolio volatility is zero.
    """

    if not isfinite(annual_risk_free_rate):
        raise ValueError(
            "Risk-free rate must be finite."
        )

    if annual_risk_free_rate <= -1:
        raise ValueError(
            "Risk-free rate must exceed -100%."
        )

    if trading_days_per_year <= 0:
        raise ValueError(
            "trading_days_per_year must be positive."
        )

    if len(daily_returns) < 2:
        raise ValueError(
            "At least two daily returns are required."
        )

    daily_risk_free_rate = (
        (1 + annual_risk_free_rate)
        ** (1 / trading_days_per_year)
        - 1
    )

    excess_returns = (
        daily_returns - daily_risk_free_rate
    )

    daily_volatility = float(
        daily_returns.std(ddof=1)
    )

    if daily_volatility == 0:
        return None

    return float(
        excess_returns.mean()
        / daily_volatility
        * sqrt(trading_days_per_year)
    )


def calculate_asset_correlations(
    prices: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate the correlation matrix of asset daily returns.
    """

    if prices.shape[1] == 0:
        raise ValueError(
            "At least one ticker is required."
        )

    aligned = validate_price_history(
        prices,
        list(prices.columns),
    )

    returns = aligned.pct_change(
        fill_method=None
    ).dropna()

    return returns.corr()


def calculate_portfolio_beta(
    portfolio_returns: pd.Series,
    benchmark_prices: pd.Series,
) -> float | None:
    """
    Calculate portfolio beta relative to a benchmark.

    Beta =
        Cov(Portfolio Returns, Benchmark Returns)
        / Var(Benchmark Returns)

    Returns None when benchmark variance is zero.
    """

    if not isinstance(benchmark_prices, pd.Series):
        raise TypeError(
            "benchmark_prices must be a pandas Series."
        )

    benchmark = benchmark_prices.sort_index()

    benchmark_returns = benchmark.pct_change(
        fill_method=None
    ).dropna()

    aligned = pd.concat(
        [
            portfolio_returns.rename("Portfolio"),
            benchmark_returns.rename("Benchmark"),
        ],
        axis=1,
        join="inner",
    ).dropna()

    if len(aligned) < 2:
        raise ValueError(
            "At least two aligned return observations "
            "are required for beta."
        )

    benchmark_variance = float(
        aligned["Benchmark"].var(ddof=1)
    )

    if benchmark_variance == 0:
        return None

    covariance = float(
        aligned["Portfolio"].cov(
            aligned["Benchmark"]
        )
    )

    return covariance / benchmark_variance


def calculate_risk_contributions(
    portfolio: StockPortfolio,
    prices: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calculate asset contributions to portfolio variance.

    Uses current portfolio weights and the historical
    covariance matrix of asset returns.

    This is a current-weight risk snapshot, not an exact
    decomposition of the historical fixed-share return
    series, whose weights change over time.

    Contribution_i =
        Weight_i × (CovarianceMatrix × Weights)_i

    Percentage contribution =
        Contribution_i / Portfolio Variance × 100
    """

    tickers = [
        holding.ticker
        for holding in portfolio.holdings
    ]

    aligned = validate_price_history(
        prices,
        tickers,
    )

    returns = aligned.pct_change(
        fill_method=None
    ).dropna()

    covariance = returns.cov().to_numpy()

    # Derive weights from the final aligned historical prices.
    # This ensures the covariance analysis reflects the portfolio's
    # actual allocation at the end of the analysis period.
    quantities = np.array(
        [holding.shares for holding in portfolio.holdings],
        dtype=float,
    )

    latest_prices = aligned.iloc[-1].to_numpy(dtype=float)
    market_values = quantities * latest_prices
    total_market_value = float(market_values.sum())

    if total_market_value <= 0:
        raise ValueError(
            "Portfolio must contain positive share quantities."
        )

    weights = market_values / total_market_value

    portfolio_variance = float(
        weights @ covariance @ weights
    )

    marginal = covariance @ weights

    contributions = weights * marginal

    if portfolio_variance <= 0:
        percentages = np.zeros(
            len(weights)
        )
    else:
        percentages = (
            contributions
            / portfolio_variance
            * 100
        )

    return pd.DataFrame(
        {
            "Ticker": tickers,
            "Weight (%)": weights * 100,
            "Variance Contribution": contributions,
            "Risk Contribution (%)": percentages,
        }
    )


def calculate_diversification_ratio(
    portfolio: StockPortfolio,
    prices: pd.DataFrame,
) -> float | None:
    """
    Calculate the portfolio diversification ratio.

    Diversification Ratio =
        Sum(weight_i × volatility_i)
        / portfolio volatility

    Uses current portfolio weights.

    Returns None when portfolio volatility is zero.
    """

    tickers = [
        holding.ticker
        for holding in portfolio.holdings
    ]

    aligned = validate_price_history(
        prices,
        tickers,
    )

    returns = aligned.pct_change(
        fill_method=None
    ).dropna()

    covariance = returns.cov().to_numpy()

    # Use final historical market values rather than stored
    # holding prices to determine the current risk weights.
    quantities = np.array(
        [holding.shares for holding in portfolio.holdings],
        dtype=float,
    )

    latest_prices = aligned.iloc[-1].to_numpy(dtype=float)
    market_values = quantities * latest_prices
    total_market_value = float(market_values.sum())

    if total_market_value <= 0:
        raise ValueError(
            "Portfolio must contain positive share quantities."
        )

    weights = market_values / total_market_value

    individual_volatilities = np.sqrt(
        np.diag(covariance)
    )

    portfolio_variance = float(
        weights @ covariance @ weights
    )

    if portfolio_variance <= 0:
        return None

    weighted_volatility = float(
        weights @ individual_volatilities
    )

    return (
        weighted_volatility
        / sqrt(portfolio_variance)
    )


def analyze_portfolio_risk(
    portfolio: StockPortfolio,
    prices: pd.DataFrame,
    benchmark_prices: pd.Series | None = None,
    annual_risk_free_rate: float = 0.0,
) -> PortfolioRiskSummary:
    """
    Run the complete historical portfolio risk analysis.

    Returns a structured PortfolioRiskSummary object.
    """

    portfolio_values = calculate_portfolio_values(
        portfolio,
        prices,
    )

    daily_returns = calculate_daily_returns(
        portfolio_values
    )

    initial_value = float(
        portfolio_values.iloc[0]
    )

    final_value = float(
        portfolio_values.iloc[-1]
    )

    total_return_pct = (
        final_value / initial_value - 1
    ) * 100

    beta = None

    if benchmark_prices is not None:
        beta = calculate_portfolio_beta(
            daily_returns,
            benchmark_prices,
        )

    diversification_ratio = (
        calculate_diversification_ratio(
            portfolio,
            prices,
        )
    )

    return PortfolioRiskSummary(
        observation_count=len(daily_returns),
        start_date=portfolio_values.index[0],
        end_date=portfolio_values.index[-1],
        initial_value=initial_value,
        final_value=final_value,
        total_return_pct=total_return_pct,
        annualized_return_pct=calculate_annualized_return(
            portfolio_values
        ),
        annualized_volatility_pct=calculate_annualized_volatility(
            daily_returns
        ),
        sharpe_ratio=calculate_sharpe_ratio(
            daily_returns,
            annual_risk_free_rate,
        ),
        maximum_drawdown_pct=calculate_maximum_drawdown(
            portfolio_values
        ),
        beta=beta,
        diversification_ratio=diversification_ratio,
    )