"""Resumable, rate-conscious stock-universe importer."""

from __future__ import annotations

import argparse
import random
import sqlite3
import time
from datetime import UTC, datetime, timedelta

from app.discovery.database import (
    DATABASE_PATH,
    database_summary,
    initialize_database,
)
from app.discovery.universe_expansion import (
    build_symbol_directory,
    fetch_and_save_company,
)


def utc_now():
    return datetime.now(UTC).isoformat()


def initialize_import_tracking():
    """Create persistent tracking for attempted symbols."""

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_PATH, timeout=30) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS import_attempts (
                ticker TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                message TEXT,
                attempts INTEGER NOT NULL DEFAULT 0,
                last_attempt_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_import_status
            ON import_attempts(status)
            """
        )


def load_existing_tickers():
    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = connection.execute(
            "SELECT ticker FROM companies"
        ).fetchall()

    return {row[0] for row in rows}


def load_attempts():
    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = connection.execute(
            """
            SELECT ticker, status, attempts, last_attempt_at
            FROM import_attempts
            """
        ).fetchall()

    return {
        ticker: {
            "status": status,
            "attempts": attempts,
            "last_attempt_at": last_attempt_at,
        }
        for ticker, status, attempts, last_attempt_at in rows
    }


def save_attempt(ticker, status, message):
    with sqlite3.connect(DATABASE_PATH, timeout=30) as connection:
        connection.execute(
            """
            INSERT INTO import_attempts (
                ticker, status, message, attempts, last_attempt_at
            )
            VALUES (?, ?, ?, 1, ?)
            ON CONFLICT(ticker) DO UPDATE SET
                status = excluded.status,
                message = excluded.message,
                attempts = import_attempts.attempts + 1,
                last_attempt_at = excluded.last_attempt_at
            """,
            (ticker, status, message, utc_now()),
        )


def eligible_for_attempt(ticker, existing, attempts, retry_days):
    if ticker in existing:
        return False

    previous = attempts.get(ticker)

    if previous is None:
        return True

    if previous["status"] == "success":
        return False

    if previous["attempts"] >= 3:
        return False

    try:
        previous_time = datetime.fromisoformat(
            previous["last_attempt_at"]
        )
        if previous_time.tzinfo is None:
            previous_time = previous_time.replace(tzinfo=UTC)
    except (ValueError, TypeError):
        return True

    return datetime.now(UTC) - previous_time >= timedelta(
        days=retry_days
    )


def import_batch(limit, delay, retry_days, seed):
    initialize_database()
    initialize_import_tracking()

    directory = build_symbol_directory()

    existing = load_existing_tickers()
    attempts = load_attempts()

    candidates = [
        (row.ticker, row.name)
        for row in directory.itertuples(index=False)
        if eligible_for_attempt(
            row.ticker,
            existing,
            attempts,
            retry_days,
        )
    ]

    random.Random(seed).shuffle(candidates)

    selected = candidates[:limit]

    print("\n===== QUANT DISCOVERY BULK IMPORT =====")
    print(f"Directory candidates: {len(directory):,}")
    print(f"Already imported: {len(existing):,}")
    print(f"Eligible candidates: {len(candidates):,}")
    print(f"Attempting this batch: {len(selected):,}")
    print()

    imported = 0
    failed = 0

    try:
        for index, (ticker, name) in enumerate(selected, 1):
            success, message = fetch_and_save_company(
                ticker,
                name,
            )

            save_attempt(
                ticker,
                "success" if success else "failed",
                message,
            )

            if success:
                imported += 1
            else:
                failed += 1

            print(
                f"[{index}/{len(selected)}] "
                f"{'OK' if success else 'SKIP':<4} "
                f"{ticker:<6} {message}",
                flush=True,
            )

            time.sleep(delay + random.uniform(0, 0.4))

    except KeyboardInterrupt:
        print("\nImport interrupted. Progress has been saved.")

    print("\n===== IMPORT SUMMARY =====")
    print(f"Imported this run: {imported}")
    print(f"Skipped this run: {failed}")
    print(
        "Total companies:",
        database_summary()["companies"],
    )

    with sqlite3.connect(DATABASE_PATH) as connection:
        rows = connection.execute(
            """
            SELECT market_cap_category, COUNT(*)
            FROM companies
            GROUP BY market_cap_category
            ORDER BY COUNT(*) DESC
            """
        ).fetchall()

    print("\nCOMPANY SIZE COVERAGE")

    for category, count in rows:
        print(f"{category}: {count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--limit",
        type=int,
        default=250,
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
    )

    parser.add_argument(
        "--retry-days",
        type=int,
        default=7,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    args = parser.parse_args()

    if args.limit < 1:
        parser.error("--limit must be positive")

    if args.delay < 0.5:
        parser.error("--delay must be at least 0.5 seconds")

    if args.retry_days < 0:
        parser.error("--retry-days cannot be negative")

    import_batch(
        limit=args.limit,
        delay=args.delay,
        retry_days=args.retry_days,
        seed=args.seed,
    )
