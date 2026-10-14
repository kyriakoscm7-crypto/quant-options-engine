"""Quant Discovery — local SQLite research database."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

LOCAL_DATABASE_PATH = (
    PROJECT_ROOT / "data" / "quant_discovery.db"
)

DEPLOYMENT_DATABASE_PATH = (
    PROJECT_ROOT
    / "deployment_data"
    / "discovery"
    / "quant_discovery_snapshot.db"
)

def select_database_path():
    """Prefer the deployed snapshot on Streamlit Cloud."""
    import os

    running_on_streamlit_cloud = (
        os.environ.get("STREAMLIT_SHARING_MODE") is not None
        or Path("/mount/src").exists()
    )

    if running_on_streamlit_cloud and DEPLOYMENT_DATABASE_PATH.exists():
        return DEPLOYMENT_DATABASE_PATH

    if LOCAL_DATABASE_PATH.exists():
        return LOCAL_DATABASE_PATH

    if DEPLOYMENT_DATABASE_PATH.exists():
        return DEPLOYMENT_DATABASE_PATH

    return LOCAL_DATABASE_PATH


DATABASE_PATH = select_database_path()


@contextmanager
def connect():
    """Open a database connection with safe transaction handling."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 5000")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def classify_market_cap(market_cap):
    """Classify company size using market capitalization in USD."""
    if market_cap is None or market_cap < 0:
        return "Unknown"
    if market_cap >= 200_000_000_000:
        return "Mega Cap"
    if market_cap >= 10_000_000_000:
        return "Large Cap"
    if market_cap >= 2_000_000_000:
        return "Mid Cap"
    if market_cap >= 300_000_000:
        return "Small Cap"
    if market_cap >= 50_000_000:
        return "Micro Cap"
    return "Nano Cap"


def initialize_database():
    """Create the initial Quant Discovery research schema."""

    with connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS companies (
                ticker TEXT PRIMARY KEY,
                name TEXT,
                sector TEXT,
                industry TEXT,
                exchange TEXT,
                market_cap REAL,
                market_cap_category TEXT,
                last_price REAL,
                is_penny_stock INTEGER DEFAULT 0,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS intelligence_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                overall_score REAL,
                technical_score REAL,
                financial_score REAL,
                growth_score REAL,
                valuation_score REAL,
                news_score REAL,
                risk_score REAL,
                methodology_version TEXT NOT NULL,
                scored_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticker) REFERENCES companies(ticker)
            );

            CREATE TABLE IF NOT EXISTS news_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                publisher TEXT,
                source_url TEXT UNIQUE,
                published_at TEXT,
                discovered_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS news_catalysts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                catalyst_type TEXT,
                sentiment TEXT,
                relevance_score REAL,
                evidence TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES news_articles(id),
                FOREIGN KEY (ticker) REFERENCES companies(ticker)
            );

            CREATE TABLE IF NOT EXISTS discovery_rankings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                category TEXT NOT NULL,
                rank_position INTEGER NOT NULL,
                score REAL,
                methodology_version TEXT NOT NULL,
                ranked_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticker) REFERENCES companies(ticker)
            );

            CREATE INDEX IF NOT EXISTS idx_company_market_cap
                ON companies(market_cap);

            CREATE INDEX IF NOT EXISTS idx_company_penny
                ON companies(is_penny_stock);

            CREATE INDEX IF NOT EXISTS idx_scores_ticker_date
                ON intelligence_scores(ticker, scored_at);

            CREATE INDEX IF NOT EXISTS idx_rankings_category_date
                ON discovery_rankings(category, ranked_at);

            CREATE INDEX IF NOT EXISTS idx_catalysts_ticker
                ON news_catalysts(ticker);
            """
        )


def upsert_company(
    ticker,
    name=None,
    sector=None,
    industry=None,
    exchange=None,
    market_cap=None,
    last_price=None,
):
    """Insert or update a company without deleting its research history."""

    ticker = ticker.strip().upper()

    if not ticker:
        raise ValueError("Ticker cannot be empty.")

    market_cap_category = classify_market_cap(market_cap)

    is_penny_stock = (
        int(last_price < 5)
        if last_price is not None and last_price > 0
        else 0
    )

    with connect() as connection:
        connection.execute(
            """
            INSERT INTO companies (
                ticker,
                name,
                sector,
                industry,
                exchange,
                market_cap,
                market_cap_category,
                last_price,
                is_penny_stock
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ticker) DO UPDATE SET
                name = COALESCE(excluded.name, companies.name),
                sector = COALESCE(excluded.sector, companies.sector),
                industry = COALESCE(excluded.industry, companies.industry),
                exchange = COALESCE(excluded.exchange, companies.exchange),
                market_cap = COALESCE(
                    excluded.market_cap, companies.market_cap
                ),
                market_cap_category = CASE
                    WHEN excluded.market_cap IS NOT NULL
                    THEN excluded.market_cap_category
                    ELSE companies.market_cap_category
                END,
                last_price = COALESCE(
                    excluded.last_price, companies.last_price
                ),
                is_penny_stock = CASE
                    WHEN excluded.last_price IS NOT NULL
                    THEN excluded.is_penny_stock
                    ELSE companies.is_penny_stock
                END,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                ticker,
                name,
                sector,
                industry,
                exchange,
                market_cap,
                market_cap_category,
                last_price,
                is_penny_stock,
            ),
        )


def search_companies(
    market_cap_category=None,
    penny_stocks_only=False,
    limit=100,
):
    """Search companies using discovery filters."""

    query = """
        SELECT *
        FROM companies
        WHERE 1 = 1
    """

    parameters = []

    if market_cap_category:
        query += " AND market_cap_category = ?"
        parameters.append(market_cap_category)

    if penny_stocks_only:
        query += " AND is_penny_stock = 1"

    query += " ORDER BY market_cap DESC LIMIT ?"
    parameters.append(max(1, min(int(limit), 1000)))

    with connect() as connection:
        rows = connection.execute(
            query, parameters
        ).fetchall()

    return [dict(row) for row in rows]


def database_summary():
    """Return basic database statistics."""

    with connect() as connection:
        companies = connection.execute(
            "SELECT COUNT(*) FROM companies"
        ).fetchone()[0]

        scores = connection.execute(
            "SELECT COUNT(*) FROM intelligence_scores"
        ).fetchone()[0]

        articles = connection.execute(
            "SELECT COUNT(*) FROM news_articles"
        ).fetchone()[0]

        catalysts = connection.execute(
            "SELECT COUNT(*) FROM news_catalysts"
        ).fetchone()[0]

    return {
        "companies": companies,
        "scores": scores,
        "articles": articles,
        "catalysts": catalysts,
    }
