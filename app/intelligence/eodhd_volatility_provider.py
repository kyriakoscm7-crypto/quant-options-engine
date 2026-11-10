"""Personal-only EODHD end-of-day cache, with durable PostgreSQL budget.

No provider request is issued unless a shared database transaction reserves its
quota first. Credentials never go into logs, URLs displayed to users, or cache.
The service must only be wired behind verified owner-only authentication.
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx
import numpy as np
import pandas as pd

API_BASE = "https://eodhd.com/api/eod/"
DAILY_BUDGET = 18  # Under provider's 20/day Free allowance.
CACHE_HOURS = 24
RETRY_HOURS = 1
MAX_ROWS = 400  # Free plan: one year; cap response size defensively.
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9.-]{1,32}$")


@dataclass(frozen=True)
class EODHDResult:
    prices: pd.DataFrame | None = None
    fetched_at: datetime | None = None
    error: str = ""
    source: str = "EODHD · adjusted daily closes"
    cached: bool = False


def eodhd_symbol(exchange_qualified: str) -> str:
    """Map validated US exchange symbols only; never guess foreign venues."""
    parts = exchange_qualified.split(":")
    if len(parts) != 2 or parts[0] not in {"NASDAQ", "NYSE", "AMEX"}:
        raise ValueError("Unsupported exchange for this EODHD personal-price integration.")
    symbol = parts[1].upper()
    if not re.fullmatch(r"[A-Z0-9][A-Z0-9.-]{0,31}", symbol):
        raise ValueError("Invalid ticker.")
    # EODHD uses BRK-B.US rather than the TradingView BRK.B representation.
    return symbol.replace(".", "-") + ".US"


def normalize_eodhd(payload):
    """Validate entire adjusted daily EOD series, rather than silently filling gaps."""
    if not isinstance(payload, list) or not 21 <= len(payload) <= MAX_ROWS:
        raise ValueError("Provider did not return sufficient daily price history.")
    rows = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Malformed daily-price observation.")
        date_value = item.get("date")
        value = item.get("adjusted_close")
        if not isinstance(date_value, str) or not isinstance(value, (int, float)):
            raise ValueError("Missing date or adjusted closing price.")
        if isinstance(value, bool) or not math.isfinite(value) or value <= 0:
            raise ValueError("Invalid adjusted closing price.")
        day = pd.to_datetime(date_value, format="%Y-%m-%d", utc=True, errors="raise")
        if day.dayofweek >= 5:
            raise ValueError("Unexpected weekend EOD bar.")
        rows.append((day, float(value)))
    frame = pd.DataFrame(rows, columns=["Date", "Close"])
    if frame["Date"].duplicated().any() or not frame["Date"].is_monotonic_increasing:
        raise ValueError("Dates must be unique and ascending.")
    # Clamp stale series: a year-old response must not appear to be fresh.
    return frame


def calculate_eodhd_hv(frame):
    """Use daily adjusted closes, sample standard deviation, sqrt(252)."""
    if not isinstance(frame, pd.DataFrame) or not {"Date", "Close"}.issubset(frame.columns):
        raise ValueError("Missing normalized daily prices.")
    returns = np.log(frame["Close"] / frame["Close"].shift(1))
    out = frame.copy()
    for window in (20, 60):
        out[f"HV{window}"] = (
            returns.rolling(window, min_periods=window).std(ddof=1)
            * math.sqrt(252) * 100
        )
    return out


class PostgresEODHDService:
    """Single shared Neon budget/cache usable from multiple Streamlit processes."""

    def __init__(self, database_url=None):
        self.database_url = database_url

    def load(self, symbol, *, api_key, now=None, client=None, database_url=None):
        if not isinstance(api_key, str) or not api_key.strip():
            return EODHDResult(error="EODHD_API_KEY is not configured.")
        if not isinstance(symbol, str) or not SYMBOL_PATTERN.fullmatch(symbol):
            return EODHDResult(error="Invalid EODHD symbol.")
        dsn = self.database_url or database_url
        if not dsn:
            return EODHDResult(error="Persistent EODHD storage is not configured.")
        now = now if now is not None else datetime.now(UTC)
        if now.tzinfo is None:
            return EODHDResult(error="Timezone-aware clock required.")
        try:
            return self._load(symbol, api_key, now, dsn, client)
        except Exception:
            # No raw exception/DSN, which could disclose secrets.
            return EODHDResult(error="EODHD cache unavailable; untracked API calls blocked.")

    def _load(self, symbol, api_key, now, dsn, client):
        import psycopg

        today = now.astimezone(UTC).date()
        with psycopg.connect(dsn, connect_timeout=4) as db:
            with db.transaction():
                db.execute(
                    "INSERT INTO eodhd_daily_budget(utc_day,calls) VALUES (%s,0) "
                    "ON CONFLICT (utc_day) DO NOTHING", (today,),
                )
                used = db.execute(
                    "SELECT calls FROM eodhd_daily_budget WHERE utc_day=%s FOR UPDATE",
                    (today,),
                ).fetchone()[0]
                row = db.execute(
                    "SELECT adjusted_payload,fetched_at,next_attempt "
                    "FROM eodhd_prices_cache WHERE symbol=%s FOR UPDATE", (symbol,),
                ).fetchone()
                if row and row[0] is not None and row[1] is not None:
                    age = now - row[1]
                    if timedelta(0) <= age < timedelta(hours=CACHE_HOURS):
                        frame = normalize_eodhd(row[0] if isinstance(row[0], list)
                                                else json.loads(row[0]))
                        return EODHDResult(
                            prices=calculate_eodhd_hv(frame), fetched_at=row[1], cached=True,
                        )
                if row and row[2] is not None and now < row[2]:
                    return EODHDResult(error="Volatility data refresh cooling down.")
                if used >= DAILY_BUDGET:
                    return EODHDResult(error="EODHD daily request budget reached.")
                # Committed reservation survives a crash before/during HTTP.
                db.execute(
                    "UPDATE eodhd_daily_budget SET calls=calls+1 WHERE utc_day=%s",
                    (today,),
                )
                db.execute(
                    "INSERT INTO eodhd_prices_cache "
                    "(symbol,adjusted_payload,fetched_at,next_attempt) "
                    "VALUES (%s,NULL,NULL,%s) "
                    "ON CONFLICT (symbol) DO UPDATE SET next_attempt=EXCLUDED.next_attempt",
                    (symbol, now + timedelta(hours=RETRY_HOURS)),
                )

        def fetch(http):
            response = http.get(
                API_BASE + symbol,
                params={"api_token": api_key, "fmt": "json", "period": "d", "order": "a"},
                timeout=12.0, follow_redirects=False,
            )
            if response.status_code != 200:
                raise ValueError("EODHD provider request failed.")
            return normalize_eodhd(response.json())

        try:
            if client is None:
                with httpx.Client() as http:
                    frame = fetch(http)
            else:
                frame = fetch(client)
        except (httpx.HTTPError, ValueError, TypeError, pd.errors.ParserError):
            return EODHDResult(error="EODHD unavailable; retry paused for one hour.")

        # Never serve stale/unreasonably old rows as fresh observations.
        if (now.date() - frame["Date"].iloc[-1].date()).days > 10:
            return EODHDResult(error="Provider prices are too old to display.")

        payload = [
            {"date": d.strftime("%Y-%m-%d"), "adjusted_close": float(c)}
            for d, c in zip(frame["Date"], frame["Close"])
        ]
        with psycopg.connect(dsn, connect_timeout=4) as db:
            with db.transaction():
                updated = db.execute(
                    "UPDATE eodhd_prices_cache "
                    "SET adjusted_payload=%s::jsonb,fetched_at=%s "
                    "WHERE symbol=%s AND next_attempt=%s",
                    (json.dumps(payload), now, symbol, now + timedelta(hours=RETRY_HOURS)),
                )
                if updated.rowcount != 1:
                    raise ValueError("Reservation was replaced.")
        return EODHDResult(
            prices=calculate_eodhd_hv(frame), fetched_at=now, cached=False,
        )


eodhd_service = PostgresEODHDService()
