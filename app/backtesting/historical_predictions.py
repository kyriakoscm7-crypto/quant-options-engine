"""Generate point-in-time ranking predictions and realized forward returns."""

from __future__ import annotations

import pandas as pd

from app.backtesting.discovery_backtest import historical_rankings

HORIZON_DAYS = {
    "5 Days": 5,
    "1 Month": 21,
    "1 Year": 252,
}


def generate_historical_predictions(
    histories: dict[str, pd.DataFrame],
    benchmark: pd.DataFrame,
    start: str = "2021-10-01",
    end: str = "2026-10-13",
) -> pd.DataFrame:
    """Evaluate historical scores against subsequent open-to-open returns.

    A signal uses prices through the signal day's close.

    Entry occurs at the next benchmark trading session's open.
    Exit occurs after the specified number of trading sessions.

    Incomplete forward periods are excluded.
    """

    calendar = pd.DatetimeIndex(benchmark.sort_index().index)

    eligible_dates = calendar[
        (calendar >= pd.Timestamp(start))
        & (calendar <= pd.Timestamp(end))
    ]

    if eligible_dates.empty:
        raise ValueError("No benchmark trading dates in the requested range.")

    monthly_dates = (
        pd.Series(eligible_dates, index=eligible_dates)
        .groupby(eligible_dates.to_period("M"))
        .first()
        .tolist()
    )

    records = []

    for signal_number, signal_date in enumerate(monthly_dates, start=1):
        print(
            f"Processing {signal_number}/{len(monthly_dates)}: "
            f"{pd.Timestamp(signal_date).date()}",
            flush=True,
        )

        signal_location = calendar.get_loc(signal_date)

        for horizon, holding_days in HORIZON_DAYS.items():
            entry_location = signal_location + 1
            exit_location = entry_location + holding_days

            if exit_location >= len(calendar):
                continue

            entry_date = calendar[entry_location]
            exit_date = calendar[exit_location]

            rankings = historical_rankings(
                histories=histories,
                as_of=signal_date,
                horizon=horizon,
            )

            if rankings.empty:
                continue

            for row in rankings.itertuples(index=False):
                ticker = row.ticker
                history = histories[ticker]

                if (
                    entry_date not in history.index
                    or exit_date not in history.index
                ):
                    continue

                entry_price = float(history.loc[entry_date, "Open"])
                exit_price = float(history.loc[exit_date, "Open"])

                if (
                    not pd.notna(entry_price)
                    or not pd.notna(exit_price)
                    or entry_price <= 0
                    or exit_price <= 0
                ):
                    continue

                records.append(
                    {
                        "date": signal_date,
                        "ticker": ticker,
                        "horizon": horizon,
                        "score": float(row.score),
                        "entry_date": entry_date,
                        "exit_date": exit_date,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "future_return": (
                            exit_price / entry_price - 1.0
                        ),
                    }
                )

    return pd.DataFrame(
        records,
        columns=[
            "date",
            "ticker",
            "horizon",
            "score",
            "entry_date",
            "exit_date",
            "entry_price",
            "exit_price",
            "future_return",
        ],
    )
