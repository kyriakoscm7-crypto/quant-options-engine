"""Historical Quant Discovery ranking and portfolio backtesting."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.discovery.ranking_pipeline import calculate_scores


@dataclass(frozen=True)
class BacktestConfig:
    initial_capital: float = 10_000.0
    top_n: int = 10
    transaction_cost: float = 0.001


def historical_rankings(
    histories: dict[str, pd.DataFrame],
    as_of: pd.Timestamp,
    horizon: str,
) -> pd.DataFrame:
    """Calculate rankings using observations available through as_of."""

    rows = []

    for ticker, history in histories.items():
        historical_data = history.loc[
            history.index <= as_of
        ]

        if historical_data.empty:
            continue

        # Exclude securities without a recent trading observation.
        # This prevents stale historical prices from entering rankings.
        latest_date = pd.Timestamp(historical_data.index[-1])
        cutoff_date = pd.Timestamp(as_of) - pd.Timedelta(days=7)

        if latest_date < cutoff_date:
            continue

        scores = calculate_scores(ticker, historical_data)

        for score in scores:
            if score["horizon"] == horizon:
                rows.append(score)

    if not rows:
        return pd.DataFrame()

    return (
        pd.DataFrame(rows)
        .sort_values(
            ["score", "ticker"],
            ascending=[False, True],
        )
        .reset_index(drop=True)
    )


def select_top_stocks(
    rankings: pd.DataFrame,
    top_n: int = 10,
) -> list[str]:
    """Select the highest-ranked eligible companies."""

    if rankings.empty:
        return []

    return rankings.head(top_n)["ticker"].tolist()


def simulate_portfolio(
    histories: dict[str, pd.DataFrame],
    benchmark: pd.DataFrame,
    rebalance_dates: list[pd.Timestamp],
    horizon: str,
    config: BacktestConfig = BacktestConfig(),
    ranking_function=None,
) -> pd.DataFrame:
    """Simulate monthly top-ranked stock portfolios.

    Rankings are calculated at each rebalance date using historical
    observations available at that time. Positions are entered at
    the next available trading session's opening price.
    """

    if config.initial_capital <= 0:
        raise ValueError("Initial capital must be positive.")

    if config.top_n <= 0:
        raise ValueError("top_n must be positive.")

    if not 0 <= config.transaction_cost < 1:
        raise ValueError("Transaction cost must be between 0 and 1.")

    if benchmark.empty:
        raise ValueError("Benchmark data cannot be empty.")

    cash = float(config.initial_capital)
    positions: dict[str, float] = {}
    records = []

    benchmark = benchmark.sort_index()
    trading_dates = benchmark.index

    for index, rebalance_date in enumerate(sorted(rebalance_dates)):
        ranker = ranking_function or historical_rankings
        rankings = ranker(histories, rebalance_date, horizon)

        selected = select_top_stocks(rankings, config.top_n)

        if not selected:
            continue

        future_dates = trading_dates[trading_dates > rebalance_date]

        if len(future_dates) == 0:
            break

        execution_date = future_dates[0]

        execution_prices = {}

        for ticker in set(positions) | set(selected):
            history = histories.get(ticker)

            if history is None or execution_date not in history.index:
                continue

            price = float(history.loc[execution_date, "Open"])

            if price > 0:
                execution_prices[ticker] = price

        # Every existing position must have an execution price.
        # Otherwise, trading would use an incomplete portfolio value.
        missing_held = set(positions) - set(execution_prices)

        if missing_held:
            raise ValueError(
                "Missing execution prices for held stocks: "
                + ", ".join(sorted(missing_held))
            )

        # Value the complete portfolio before making any trades.
        portfolio_value = cash + sum(
            shares * execution_prices[ticker]
            for ticker, shares in positions.items()
        )

        available = [
            ticker for ticker in selected
            if ticker in execution_prices
        ]

        if not available:
            raise ValueError(
                "No selected stocks have valid execution prices."
            )

        # Allocate equally across the stocks we can actually trade.
        target_value = portfolio_value / len(available)

        # Sell unwanted holdings and reduce overweight positions first.
        # Selling before buying ensures cash is available.
        for ticker, shares in list(positions.items()):
            price = execution_prices[ticker]
            current_value = shares * price

            desired_value = (
                target_value if ticker in available else 0.0
            )

            excess_value = current_value - desired_value

            if excess_value > 1e-9:
                shares_to_sell = excess_value / price

                cash += (
                    excess_value
                    * (1 - config.transaction_cost)
                )

                remaining = shares - shares_to_sell

                if remaining <= 1e-12:
                    del positions[ticker]
                else:
                    positions[ticker] = remaining

        # Allocate available cash toward underweight positions.
        # Trading costs are included in the purchase budget.
        deficits = {}

        for ticker in available:
            price = execution_prices[ticker]
            current_value = positions.get(ticker, 0.0) * price

            deficit = max(0.0, target_value - current_value)

            if deficit > 1e-9:
                deficits[ticker] = deficit

        total_deficit = sum(deficits.values())

        if total_deficit > 0:
            affordable_notional = cash / (
                1 + config.transaction_cost
            )

            scale = min(
                1.0,
                affordable_notional / total_deficit,
            )

            for ticker, deficit in deficits.items():
                price = execution_prices[ticker]
                purchase_value = deficit * scale
                cost = purchase_value * (
                    1 + config.transaction_cost
                )

                positions[ticker] = (
                    positions.get(ticker, 0.0)
                    + purchase_value / price
                )

                cash -= cost

        # Small negative values caused by floating-point rounding
        # are treated as zero, but meaningful deficits are errors.
        if cash < -1e-7:
            raise ValueError(
                "Rebalancing created a negative cash balance."
            )

        cash = max(0.0, cash)

        if index + 1 < len(rebalance_dates):
            next_date = sorted(rebalance_dates)[index + 1]
            period_dates = trading_dates[
                (trading_dates >= execution_date)
                & (trading_dates <= next_date)
            ]
        else:
            period_dates = trading_dates[
                trading_dates >= execution_date
            ]

        for date in period_dates:
            value = cash

            for ticker, shares in positions.items():
                history = histories.get(ticker)

                if history is None:
                    raise ValueError(
                        f"Missing price history for held stock {ticker}"
                    )

                available = history.loc[history.index <= date, "Close"].dropna()

                if available.empty:
                    raise ValueError(
                        f"No historical closing price for {ticker} on {date}"
                    )

                value += shares * float(available.iloc[-1])

            position_values = {}

            for ticker, shares in positions.items():
                history = histories[ticker]

                available = history.loc[
                    history.index <= date, "Close"
                ].dropna()

                if available.empty:
                    raise ValueError(
                        f"No valuation price for {ticker} on {date}"
                    )

                position_values[ticker] = (
                    shares * float(available.iloc[-1])
                )

            records.append(
                {
                    "Date": date,
                    "Portfolio Value": value,
                    "Horizon": horizon,
                    "Holdings": ", ".join(sorted(positions)),
                    "Cash": cash,
                    "Position Values": position_values,
                }
            )

    if not records:
        return pd.DataFrame(
            columns=[
                "Date",
                "Portfolio Value",
                "Horizon",
                "Holdings",
            ]
        )

    return (
        pd.DataFrame(records)
        .drop_duplicates(subset=["Date"], keep="last")
        .sort_values("Date")
        .reset_index(drop=True)
    )
