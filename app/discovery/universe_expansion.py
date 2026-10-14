"""Expand Quant Discovery using Nasdaq's public symbol directory."""

from __future__ import annotations

import argparse
import io
import random
import time
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf

from app.discovery.database import (
    connect,
    database_summary,
    initialize_database,
    upsert_company,
)

DIRECTORY_URLS = {
    "nasdaq": (
        "https://www.nasdaqtrader.com/dynamic/"
        "SymDir/nasdaqlisted.txt"
    ),
    "other": (
        "https://www.nasdaqtrader.com/dynamic/"
        "SymDir/otherlisted.txt"
    ),
}

CACHE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "discovery_symbol_directory.csv"
)

EXCLUDED_NAME_TERMS = (
    " ETF",
    " ETN",
    " WARRANT",
    " WARRANTS",
    " RIGHTS",
    " UNIT",
    " UNITS",
    " PREFERRED",
    " PREFERENCE",
    " DEPOSITARY",
    " DEPOSITORY",
    " NOTES DUE",
    " BOND",
    " TRUST PREFERRED",
)


def download_directory(url: str) -> pd.DataFrame:
    """Download and parse a Nasdaq Trader symbol directory."""

    response = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "QuantDiscoveryResearch/1.0"},
    )
    response.raise_for_status()

    frame = pd.read_csv(
        io.StringIO(response.text),
        sep="|",
        dtype=str,
    )

    return frame.fillna("")


def build_symbol_directory(refresh: bool = False) -> pd.DataFrame:
    """Create a deduplicated stock-symbol candidate universe."""

    if CACHE_PATH.exists() and not refresh:
        frame = pd.read_csv(CACHE_PATH, dtype=str).fillna("")
        print(f"Loaded cached directory: {len(frame):,} symbols")
        return frame

    print("Downloading Nasdaq-listed symbols...")
    nasdaq = download_directory(DIRECTORY_URLS["nasdaq"])

    print("Downloading other exchange-listed symbols...")
    other = download_directory(DIRECTORY_URLS["other"])

    nasdaq = nasdaq.rename(
        columns={
            "Symbol": "ticker",
            "Security Name": "name",
            "ETF": "etf",
            "Test Issue": "test_issue",
        }
    )

    other = other.rename(
        columns={
            "ACT Symbol": "ticker",
            "Security Name": "name",
            "ETF": "etf",
            "Test Issue": "test_issue",
        }
    )

    frames = []

    for frame in (nasdaq, other):
        required = {"ticker", "name", "etf", "test_issue"}

        if not required.issubset(frame.columns):
            raise ValueError(
                "Nasdaq directory format changed: "
                f"{required - set(frame.columns)}"
            )

        frame = frame[
            (frame["etf"].str.upper() == "N")
            & (frame["test_issue"].str.upper() == "N")
        ].copy()

        frames.append(frame[["ticker", "name"]])

    universe = pd.concat(frames, ignore_index=True)

    universe["ticker"] = universe["ticker"].str.strip().str.upper()
    universe["name"] = universe["name"].str.strip()

    universe = universe[
        universe["ticker"].str.fullmatch(r"[A-Z]{1,5}")
    ].copy()

    upper_names = universe["name"].str.upper()

    excluded = upper_names.apply(
        lambda name: any(
            term in f" {name} "
            for term in EXCLUDED_NAME_TERMS
        )
    )

    universe = universe[~excluded].copy()

    universe = universe.drop_duplicates(
        subset="ticker",
        keep="first",
    )

    universe = universe.sort_values("ticker").reset_index(drop=True)

    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    universe.to_csv(CACHE_PATH, index=False)

    print(f"Candidate symbols saved: {len(universe):,}")

    return universe


def existing_tickers() -> set[str]:
    """Return tickers already stored in the local database."""

    with connect() as connection:
        rows = connection.execute(
            "SELECT ticker FROM companies"
        ).fetchall()

    return {row["ticker"] for row in rows}


def fetch_and_save_company(
    ticker: str,
    directory_name: str,
) -> tuple[bool, str]:
    """Retrieve company fundamentals and save valid records."""

    try:
        info = yf.Ticker(ticker).info

        if not isinstance(info, dict) or not info:
            return False, "No company data"

        quote_type = str(
            info.get("quoteType") or ""
        ).upper()

        if quote_type not in {"EQUITY", ""}:
            return False, f"Excluded quote type: {quote_type}"

        market_cap = info.get("marketCap")
        price = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
        )

        if not isinstance(market_cap, (int, float)):
            return False, "Missing market cap"

        if market_cap <= 0:
            return False, "Invalid market cap"

        if not isinstance(price, (int, float)) or price <= 0:
            return False, "Missing valid stock price"

        name = (
            info.get("longName")
            or info.get("shortName")
            or directory_name
        )

        upsert_company(
            ticker=ticker,
            name=name,
            sector=info.get("sector"),
            industry=info.get("industry"),
            exchange=info.get("exchange"),
            market_cap=market_cap,
            last_price=price,
        )

        if market_cap < 50_000_000:
            category = "Nano Cap"
        elif market_cap < 300_000_000:
            category = "Micro Cap"
        elif market_cap < 2_000_000_000:
            category = "Small Cap"
        elif market_cap < 10_000_000_000:
            category = "Mid Cap"
        elif market_cap < 200_000_000_000:
            category = "Large Cap"
        else:
            category = "Mega Cap"

        return True, f"{category} | ${price:.2f}"

    except Exception as exc:
        return False, str(exc)[:100]


def expand_universe(
    limit: int = 100,
    refresh_directory: bool = False,
    seed: int = 42,
):
    """Import a controlled batch of new companies."""

    initialize_database()

    universe = build_symbol_directory(
        refresh=refresh_directory
    )

    already_saved = existing_tickers()

    candidates = universe[
        ~universe["ticker"].isin(already_saved)
    ].copy()

    candidates = candidates.sample(
        frac=1,
        random_state=seed,
    ).reset_index(drop=True)

    print(f"\nExisting companies: {len(already_saved):,}")
    print(f"Available new candidates: {len(candidates):,}")
    print(f"Maximum symbols to attempt: {limit:,}\n")

    successful = 0
    attempted = 0

    for row in candidates.itertuples(index=False):
        if attempted >= limit:
            break

        ticker = row.ticker
        name = row.name

        attempted += 1

        success, message = fetch_and_save_company(
            ticker,
            name,
        )

        status = "OK" if success else "SKIP"

        print(
            f"[{attempted}/{limit}] "
            f"{status:<4} {ticker:<6} {message}",
            flush=True,
        )

        if success:
            successful += 1

        time.sleep(random.uniform(0.5, 1.0))

    print("\n===== QUANT DISCOVERY EXPANSION =====")
    print(f"Attempted: {attempted}")
    print(f"Imported: {successful}")
    print(f"Total companies: {database_summary()['companies']}")

    with connect() as connection:
        rows = connection.execute(
            """
            SELECT market_cap_category, COUNT(*) AS total
            FROM companies
            GROUP BY market_cap_category
            ORDER BY total DESC
            """
        ).fetchall()

    print("\nCOMPANY SIZE COVERAGE")

    for row in rows:
        print(
            f"{row['market_cap_category']}: "
            f"{row['total']}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--limit",
        type=int,
        default=100,
    )

    parser.add_argument(
        "--refresh-directory",
        action="store_true",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    arguments = parser.parse_args()

    if arguments.limit < 1:
        parser.error("--limit must be at least 1")

    expand_universe(
        limit=arguments.limit,
        refresh_directory=arguments.refresh_directory,
        seed=arguments.seed,
    )
