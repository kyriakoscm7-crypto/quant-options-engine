"""Quant Discovery — stock universe importer."""

from __future__ import annotations

import time

import yfinance as yf

from app.discovery.database import (
    database_summary,
    initialize_database,
    upsert_company,
)

STARTER_TICKERS = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN",
    "META", "TSLA", "AVGO", "AMD", "NFLX",
    "PLTR", "CRM", "ORCL", "INTC", "UBER",
    "SOFI", "RKLB", "IONQ", "HIMS", "HOOD",
    "RIVN", "LCID", "ACHR", "JOBY", "SOUN",
]


def import_company(ticker: str) -> bool:
    """Fetch company information and store it in the database."""

    try:
        info = yf.Ticker(ticker).info

        if not isinstance(info, dict) or not info:
            print(f"SKIP {ticker}: no company information")
            return False

        name = info.get("longName") or info.get("shortName")

        market_cap = info.get("marketCap")
        last_price = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
        )

        if not name:
            print(f"SKIP {ticker}: missing company name")
            return False

        upsert_company(
            ticker=ticker,
            name=name,
            sector=info.get("sector"),
            industry=info.get("industry"),
            exchange=info.get("exchange"),
            market_cap=market_cap,
            last_price=last_price,
        )

        print(
            f"OK   {ticker:<6} "
            f"${last_price:.2f} "
            if isinstance(last_price, (int, float))
            else f"OK   {ticker:<6} price unavailable"
        )

        return True

    except Exception as exc:
        print(f"FAIL {ticker}: {exc}")
        return False


def import_starter_universe():
    """Import a small, diverse starting collection of companies."""

    initialize_database()

    successes = 0

    for index, ticker in enumerate(STARTER_TICKERS, start=1):
        print(f"[{index}/{len(STARTER_TICKERS)}] ", end="")

        if import_company(ticker):
            successes += 1

        time.sleep(0.5)

    print("\n===== IMPORT COMPLETE =====")
    print(f"Successfully imported: {successes}")
    print(f"Attempted: {len(STARTER_TICKERS)}")

    summary = database_summary()

    print(f"Companies in database: {summary['companies']}")


if __name__ == "__main__":
    import_starter_universe()
