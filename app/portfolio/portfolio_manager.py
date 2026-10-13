"""
Quant Intelligence — Stock Portfolio Manager.

This module provides the foundational calculations for
managing and analyzing a portfolio of stock holdings.

Features:
- Stock holding validation.
- Fractional share support.
- Individual holding valuations.
- Total portfolio market value.
- Portfolio allocation percentages.
- Portfolio concentration analysis.
- Structured portfolio summaries.

Prices are supplied explicitly.

This allows deterministic calculations and testing
without depending on external market data.

Future modules will integrate Yahoo Finance market data,
historical performance, and portfolio risk analytics.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from math import isfinite

import pandas as pd

from app.market_data.stock_history import validate_ticker

# ============================================================
# STOCK HOLDING
# ============================================================


@dataclass(frozen=True)
class StockHolding:
    """
    Represent a single stock position.

    Attributes:
        ticker:
            Stock ticker symbol.

        shares:
            Number of shares owned.

            Fractional shares are supported.

        price:
            Current price per share.

    Example:
        StockHolding(
            ticker="AAPL",
            shares=10,
            price=250,
        )
    """

    ticker: str
    shares: float
    price: float

    def __post_init__(self) -> None:
        """
        Validate and normalize the holding.

        Since this dataclass is frozen, object.__setattr__
        is required to normalize its attributes.
        """

        normalized_ticker = validate_ticker(
            self.ticker
        )

        object.__setattr__(
            self,
            "ticker",
            normalized_ticker,
        )

        for field_name in ("shares", "price"):

            value = getattr(
                self,
                field_name,
            )

            if isinstance(value, bool):

                raise ValueError(
                    f"{field_name} must be a valid number."
                )

            try:

                numeric_value = float(value)

            except (TypeError, ValueError) as exc:

                raise ValueError(
                    f"{field_name} must be a valid number."
                ) from exc

            if not isfinite(numeric_value):

                raise ValueError(
                    f"{field_name} must be finite."
                )

            if numeric_value < 0:

                raise ValueError(
                    f"{field_name} cannot be negative."
                )

            object.__setattr__(
                self,
                field_name,
                numeric_value,
            )

    @property
    def market_value(self) -> float:
        """
        Calculate the current market value of the holding.

        Market Value = Shares × Price
        """

        return self.shares * self.price


# ============================================================
# STOCK PORTFOLIO
# ============================================================


class StockPortfolio:
    """
    Represent a collection of stock holdings.

    The portfolio combines holdings, calculates their
    market values, and determines allocation percentages.

    Duplicate tickers are combined automatically when
    their supplied prices match.

    A duplicate ticker with conflicting prices raises
    ValueError to avoid ambiguous valuations.
    """

    def __init__(
        self,
        holdings: Iterable[StockHolding],
    ) -> None:
        """
        Initialize a stock portfolio.
        """

        try:

            supplied_holdings = list(holdings)

        except TypeError as exc:

            raise ValueError(
                "holdings must be an iterable of StockHolding objects."
            ) from exc

        combined: dict[str, StockHolding] = {}

        for holding in supplied_holdings:

            if not isinstance(
                holding,
                StockHolding,
            ):

                raise TypeError(
                    "Every holding must be a StockHolding object."
                )

            if holding.ticker not in combined:

                combined[holding.ticker] = holding

                continue

            existing = combined[holding.ticker]

            if existing.price != holding.price:

                raise ValueError(
                    f"Conflicting prices for {holding.ticker}."
                )

            combined[holding.ticker] = StockHolding(
                ticker=holding.ticker,
                shares=existing.shares + holding.shares,
                price=holding.price,
            )

        self._holdings = tuple(
            combined.values()
        )

    @property
    def holdings(self) -> tuple[StockHolding, ...]:
        """
        Return the portfolio holdings.
        """

        return self._holdings

    @property
    def holding_count(self) -> int:
        """
        Return the number of unique stock holdings.
        """

        return len(self._holdings)

    @property
    def total_value(self) -> float:
        """
        Calculate the total portfolio market value.
        """

        return sum(
            holding.market_value
            for holding in self._holdings
        )

    @property
    def largest_holding(self) -> StockHolding | None:
        """
        Return the holding with the largest market value.

        Returns None when the portfolio is empty.
        """

        if not self._holdings:

            return None

        return max(
            self._holdings,
            key=lambda holding: holding.market_value,
        )

    @property
    def smallest_holding(self) -> StockHolding | None:
        """
        Return the holding with the smallest market value.

        Returns None when the portfolio is empty.
        """

        if not self._holdings:

            return None

        return min(
            self._holdings,
            key=lambda holding: holding.market_value,
        )

    def to_dataframe(self) -> pd.DataFrame:
        """
        Convert the portfolio into a structured DataFrame.

        Columns:
            Ticker
            Shares
            Price
            Market Value
            Allocation (%)
        """

        total = self.total_value

        rows = []

        for holding in self._holdings:

            market_value = holding.market_value

            allocation = (
                market_value / total * 100
                if total > 0
                else 0.0
            )

            rows.append(
                {
                    "Ticker": holding.ticker,
                    "Shares": holding.shares,
                    "Price": holding.price,
                    "Market Value": market_value,
                    "Allocation (%)": allocation,
                }
            )

        columns = [
            "Ticker",
            "Shares",
            "Price",
            "Market Value",
            "Allocation (%)",
        ]

        return pd.DataFrame(
            rows,
            columns=columns,
        )

    def allocation_by_ticker(self) -> dict[str, float]:
        """
        Return each holding's percentage allocation.
        """

        total = self.total_value

        if total == 0:

            return {
                holding.ticker: 0.0
                for holding in self._holdings
            }

        return {
            holding.ticker: (
                holding.market_value / total * 100
            )
            for holding in self._holdings
        }

    def concentration(self) -> float:
        """
        Calculate the largest holding's portfolio weight.

        Example:
            If AAPL represents 40% of the portfolio,
            concentration() returns 40.0.
        """

        if self.total_value == 0:

            return 0.0

        largest = self.largest_holding

        if largest is None:

            return 0.0

        return (
            largest.market_value
            / self.total_value
            * 100
        )

    def summary(self) -> dict[str, object]:
        """
        Return a structured summary of the portfolio.
        """

        largest = self.largest_holding
        smallest = self.smallest_holding

        return {
            "holding_count": self.holding_count,
            "total_value": self.total_value,
            "largest_holding": (
                largest.ticker
                if largest is not None
                else None
            ),
            "smallest_holding": (
                smallest.ticker
                if smallest is not None
                else None
            ),
            "concentration_pct": self.concentration(),
        }