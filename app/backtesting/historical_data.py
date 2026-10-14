"""Historical price data utilities for Quant Discovery backtesting."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import yfinance as yf


def download_historical_prices(
    tickers: list[str],
    start: str = "2020-10-01",
    end: str | None = None,
    batch_size: int = 25,
) -> dict[str, pd.DataFrame]:
    """Download adjusted daily OHLCV data in manageable batches."""

    if batch_size < 1:
        raise ValueError("batch_size must be positive.")

    unique_tickers = list(dict.fromkeys(tickers))

    histories: dict[str, pd.DataFrame] = {}

    for offset in range(0, len(unique_tickers), batch_size):
        batch = unique_tickers[offset:offset + batch_size]

        print(
            f"Downloading {offset + 1}-"
            f"{min(offset + batch_size, len(unique_tickers))}"
            f" of {len(unique_tickers)} tickers..."
        )

        data = yf.download(
            tickers=batch,
            start=start,
            end=end,
            interval="1d",
            auto_adjust=True,
            group_by="ticker",
            threads=True,
            progress=False,
        )

        for ticker in batch:
            if isinstance(data.columns, pd.MultiIndex):
                if ticker not in data.columns.get_level_values(0):
                    continue
                history = data[ticker].copy()
            elif len(batch) == 1:
                history = data.copy()
            else:
                continue

            if "Close" not in history:
                continue

            history = history.dropna(subset=["Close"])

            if not history.empty:
                histories[ticker] = history.sort_index()

    return histories


def save_historical_prices(
    histories: dict[str, pd.DataFrame],
    directory: str = "deployment_data/backtesting",
) -> None:
    """Save downloaded histories as CSV files."""

    output = Path(directory)
    output.mkdir(parents=True, exist_ok=True)

    for ticker, history in histories.items():
        safe_ticker = ticker.replace("/", "_").replace("\\", "_")
        history.to_csv(output / f"{safe_ticker}.csv")


def load_historical_prices(
    data_dir="deployment_data/backtesting",
):
    """Load historical OHLCV files, excluding research report CSVs."""

    from pathlib import Path

    import pandas as pd

    data_dir = Path(data_dir)

    histories = {}

    required_columns = {
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    }

    for path in sorted(data_dir.glob("*.csv")):
        history = pd.read_csv(
            path,
            index_col=0,
            parse_dates=True,
        )

        if not required_columns.issubset(history.columns):
            continue

        if history.empty:
            continue

        history = history.sort_index()

        histories[path.stem] = history

    return histories


def default_end_date() -> str:
    """Return today's date for optional download boundaries."""
    return date.today().isoformat()
