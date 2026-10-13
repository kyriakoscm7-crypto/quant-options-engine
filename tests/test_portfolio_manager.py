"""
Automated tests for the Quant Intelligence Stock Portfolio Manager.

Tests cover:
- Holding creation and normalization.
- Fractional shares.
- Holding market values.
- Invalid input validation.
- Portfolio construction.
- Duplicate ticker handling.
- Portfolio valuation.
- Portfolio allocations.
- Concentration.
- Empty portfolios.
- Portfolio summaries.
- DataFrame output.
"""

import math

import pandas as pd
import pytest

from app.portfolio.portfolio_manager import StockHolding, StockPortfolio

# ============================================================
# STOCK HOLDING TESTS
# ============================================================


def test_holding_creation():
    holding = StockHolding("AAPL", 10, 250)

    assert holding.ticker == "AAPL"
    assert holding.shares == 10.0
    assert holding.price == 250.0


def test_holding_normalizes_ticker():
    holding = StockHolding(" aapl ", 10, 250)

    assert holding.ticker == "AAPL"


def test_holding_supports_fractional_shares():
    holding = StockHolding("NVDA", 2.5, 150)

    assert holding.shares == 2.5
    assert holding.market_value == 375.0


def test_holding_market_value():
    holding = StockHolding("MSFT", 5, 500)

    assert holding.market_value == 2500.0


def test_holding_supports_zero_shares():
    holding = StockHolding("AAPL", 0, 250)

    assert holding.market_value == 0.0


def test_holding_supports_zero_price():
    holding = StockHolding("AAPL", 10, 0)

    assert holding.market_value == 0.0


@pytest.mark.parametrize(
    "shares",
    [
        -1,
        -0.5,
        float("nan"),
        float("inf"),
        float("-inf"),
        None,
        "invalid",
        True,
        False,
    ],
)
def test_holding_rejects_invalid_shares(shares):
    with pytest.raises(ValueError):
        StockHolding("AAPL", shares, 250)


@pytest.mark.parametrize(
    "price",
    [
        -1,
        -0.01,
        float("nan"),
        float("inf"),
        float("-inf"),
        None,
        "invalid",
        True,
        False,
    ],
)
def test_holding_rejects_invalid_prices(price):
    with pytest.raises(ValueError):
        StockHolding("AAPL", 10, price)


@pytest.mark.parametrize(
    "ticker",
    [
        "",
        " ",
        None,
        123,
    ],
)
def test_holding_rejects_invalid_tickers(ticker):
    with pytest.raises((TypeError, ValueError)):
        StockHolding(ticker, 10, 250)


def test_holding_is_immutable():
    holding = StockHolding("AAPL", 10, 250)

    with pytest.raises(AttributeError):
        holding.shares = 20


# ============================================================
# PORTFOLIO CONSTRUCTION TESTS
# ============================================================


def test_portfolio_creation():
    portfolio = StockPortfolio(
        [
            StockHolding("AAPL", 10, 250),
            StockHolding("MSFT", 5, 500),
        ]
    )

    assert portfolio.holding_count == 2


def test_portfolio_accepts_generator():
    holdings = (
        StockHolding(ticker, shares, price)
        for ticker, shares, price in [
            ("AAPL", 10, 250),
            ("MSFT", 5, 500),
        ]
    )

    portfolio = StockPortfolio(holdings)

    assert portfolio.holding_count == 2


def test_portfolio_rejects_non_iterable():
    with pytest.raises(ValueError):
        StockPortfolio(None)


def test_portfolio_rejects_invalid_holding_objects():
    with pytest.raises(TypeError):
        StockPortfolio(
            [
                StockHolding("AAPL", 10, 250),
                "MSFT",
            ]
        )


def test_portfolio_combines_duplicate_tickers():
    portfolio = StockPortfolio(
        [
            StockHolding("AAPL", 10, 250),
            StockHolding("AAPL", 5, 250),
        ]
    )

    assert portfolio.holding_count == 1
    assert portfolio.holdings[0].shares == 15.0
    assert portfolio.total_value == 3750.0


def test_portfolio_combines_normalized_duplicate_tickers():
    portfolio = StockPortfolio(
        [
            StockHolding("aapl", 10, 250),
            StockHolding("AAPL", 5, 250),
        ]
    )

    assert portfolio.holding_count == 1
    assert portfolio.holdings[0].ticker == "AAPL"
    assert portfolio.holdings[0].shares == 15.0


def test_portfolio_rejects_conflicting_duplicate_prices():
    with pytest.raises(ValueError, match="Conflicting prices"):
        StockPortfolio(
            [
                StockHolding("AAPL", 10, 250),
                StockHolding("AAPL", 5, 260),
            ]
        )


def test_portfolio_holdings_are_tuple():
    portfolio = StockPortfolio(
        [StockHolding("AAPL", 10, 250)]
    )

    assert isinstance(portfolio.holdings, tuple)


# ============================================================
# PORTFOLIO VALUATION TESTS
# ============================================================


@pytest.fixture
def sample_portfolio():
    return StockPortfolio(
        [
            StockHolding("AAPL", 10, 250),
            StockHolding("MSFT", 5, 500),
            StockHolding("NVDA", 20, 150),
            StockHolding("GOOGL", 8, 200),
        ]
    )


def test_portfolio_total_value(sample_portfolio):
    assert sample_portfolio.total_value == 9600.0


def test_portfolio_holding_count(sample_portfolio):
    assert sample_portfolio.holding_count == 4


def test_portfolio_largest_holding(sample_portfolio):
    assert sample_portfolio.largest_holding.ticker == "NVDA"


def test_portfolio_smallest_holding(sample_portfolio):
    assert sample_portfolio.smallest_holding.ticker == "GOOGL"


def test_portfolio_allocation_values(sample_portfolio):
    allocations = sample_portfolio.allocation_by_ticker()

    assert allocations["AAPL"] == pytest.approx(
        2500 / 9600 * 100
    )

    assert allocations["MSFT"] == pytest.approx(
        2500 / 9600 * 100
    )

    assert allocations["NVDA"] == pytest.approx(
        3000 / 9600 * 100
    )

    assert allocations["GOOGL"] == pytest.approx(
        1600 / 9600 * 100
    )


def test_portfolio_allocations_sum_to_100(sample_portfolio):
    allocations = sample_portfolio.allocation_by_ticker()

    assert sum(allocations.values()) == pytest.approx(100.0)


def test_portfolio_concentration(sample_portfolio):
    assert sample_portfolio.concentration() == pytest.approx(
        31.25
    )


def test_portfolio_summary(sample_portfolio):
    summary = sample_portfolio.summary()

    assert summary["holding_count"] == 4
    assert summary["total_value"] == 9600.0
    assert summary["largest_holding"] == "NVDA"
    assert summary["smallest_holding"] == "GOOGL"
    assert summary["concentration_pct"] == 31.25


# ============================================================
# DATAFRAME TESTS
# ============================================================


def test_portfolio_dataframe_type(sample_portfolio):
    result = sample_portfolio.to_dataframe()

    assert isinstance(result, pd.DataFrame)


def test_portfolio_dataframe_columns(sample_portfolio):
    result = sample_portfolio.to_dataframe()

    assert list(result.columns) == [
        "Ticker",
        "Shares",
        "Price",
        "Market Value",
        "Allocation (%)",
    ]


def test_portfolio_dataframe_row_count(sample_portfolio):
    result = sample_portfolio.to_dataframe()

    assert len(result) == 4


def test_portfolio_dataframe_market_values(sample_portfolio):
    result = sample_portfolio.to_dataframe()

    values = dict(
        zip(
            result["Ticker"],
            result["Market Value"],
            strict=True,
        )
    )

    assert values == {
        "AAPL": 2500.0,
        "MSFT": 2500.0,
        "NVDA": 3000.0,
        "GOOGL": 1600.0,
    }


def test_portfolio_dataframe_allocations_sum_to_100(
    sample_portfolio,
):
    result = sample_portfolio.to_dataframe()

    assert result["Allocation (%)"].sum() == pytest.approx(
        100.0
    )


# ============================================================
# EMPTY PORTFOLIO TESTS
# ============================================================


def test_empty_portfolio():
    portfolio = StockPortfolio([])

    assert portfolio.holding_count == 0
    assert portfolio.total_value == 0.0


def test_empty_portfolio_largest_holding():
    portfolio = StockPortfolio([])

    assert portfolio.largest_holding is None


def test_empty_portfolio_smallest_holding():
    portfolio = StockPortfolio([])

    assert portfolio.smallest_holding is None


def test_empty_portfolio_allocations():
    portfolio = StockPortfolio([])

    assert portfolio.allocation_by_ticker() == {}


def test_empty_portfolio_concentration():
    portfolio = StockPortfolio([])

    assert portfolio.concentration() == 0.0


def test_empty_portfolio_dataframe():
    portfolio = StockPortfolio([])

    result = portfolio.to_dataframe()

    assert result.empty
    assert len(result.columns) == 5


def test_empty_portfolio_summary():
    portfolio = StockPortfolio([])

    summary = portfolio.summary()

    assert summary["holding_count"] == 0
    assert summary["total_value"] == 0.0
    assert summary["largest_holding"] is None
    assert summary["smallest_holding"] is None
    assert summary["concentration_pct"] == 0.0


# ============================================================
# ZERO-VALUE PORTFOLIO TESTS
# ============================================================


def test_zero_value_portfolio():
    portfolio = StockPortfolio(
        [
            StockHolding("AAPL", 0, 250),
            StockHolding("MSFT", 0, 500),
        ]
    )

    assert portfolio.total_value == 0.0
    assert portfolio.holding_count == 2


def test_zero_value_portfolio_allocations():
    portfolio = StockPortfolio(
        [
            StockHolding("AAPL", 0, 250),
            StockHolding("MSFT", 0, 500),
        ]
    )

    assert portfolio.allocation_by_ticker() == {
        "AAPL": 0.0,
        "MSFT": 0.0,
    }


def test_zero_value_portfolio_concentration():
    portfolio = StockPortfolio(
        [
            StockHolding("AAPL", 0, 250),
            StockHolding("MSFT", 0, 500),
        ]
    )

    assert portfolio.concentration() == 0.0


def test_zero_value_portfolio_dataframe_allocations():
    portfolio = StockPortfolio(
        [
            StockHolding("AAPL", 0, 250),
            StockHolding("MSFT", 0, 500),
        ]
    )

    result = portfolio.to_dataframe()

    assert result["Allocation (%)"].tolist() == [
        0.0,
        0.0,
    ]


# ============================================================
# ADDITIONAL EDGE CASES
# ============================================================


def test_single_holding_allocation():
    portfolio = StockPortfolio(
        [StockHolding("AAPL", 10, 250)]
    )

    assert portfolio.allocation_by_ticker() == {
        "AAPL": 100.0,
    }


def test_single_holding_concentration():
    portfolio = StockPortfolio(
        [StockHolding("AAPL", 10, 250)]
    )

    assert portfolio.concentration() == 100.0


def test_fractional_portfolio_value():
    portfolio = StockPortfolio(
        [
            StockHolding("AAPL", 1.5, 200),
            StockHolding("NVDA", 2.25, 100),
        ]
    )

    assert portfolio.total_value == 525.0


def test_holding_market_value_is_finite():
    holding = StockHolding("AAPL", 10, 250)

    assert math.isfinite(holding.market_value)