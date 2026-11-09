"""EarningsAPI.com calendar adapter for the public earnings page.

The provider supplies date/session buckets, not company-confirmed schedules.
No third-party feed is exposed to clients; only the rendered calendar is displayed.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx

API_URL = "https://api.earningsapi.com/v2/calendar/earnings"
CACHE_SECONDS = 7 * 24 * 60 * 60
RETRY_SECONDS = 24 * 60 * 60
MONTHLY_REQUEST_BUDGET = 250
WEEK_REQUESTS = 7
ET = ZoneInfo("America/New_York")
SYMBOL = re.compile(r"[A-Z][A-Z0-9.\-]{0,14}\Z")
SESSIONS = {
    "pre": "Before market",
    "after": "After market",
    "notSupplied": "Time not supplied",
}


@dataclass(frozen=True)
class EarningsEvent:
    symbol: str
    name: str
    day: date
    session: str
    eps_estimate: float | None = None
    revenue_estimate: float | None = None


@dataclass(frozen=True)
class WeekResult:
    events: tuple[EarningsEvent, ...] = ()
    error: str = ""
    retrieved_at: float | None = None
    rejected: int = 0
    cache_expires_at: float | None = None


def _optional_number(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        from math import isfinite
        result = float(value)
        return result if isfinite(result) else None
    except (TypeError, ValueError, OverflowError):
        return None


def normalize_day(payload, expected_day):
    """Validate and normalize only entries for the requested date."""
    if not isinstance(payload, dict) or payload.get("date") != expected_day.isoformat():
        raise ValueError("Unexpected calendar response date")
    if not all(isinstance(payload.get(group), list) for group in SESSIONS):
        raise ValueError("Missing earnings-session lists")
    events = {}
    rejected = 0
    for group, session in SESSIONS.items():
        for item in payload[group]:
            if not isinstance(item, dict):
                rejected += 1
                continue
            raw = item.get("symbol")
            symbol = raw.strip().upper() if isinstance(raw, str) else ""
            if not SYMBOL.fullmatch(symbol):
                rejected += 1
                continue
            name = item.get("name")
            name = name.strip()[:120] if isinstance(name, str) and name.strip() else symbol
            event = EarningsEvent(
                symbol=symbol,
                name=name,
                day=expected_day,
                session=session,
                eps_estimate=_optional_number(item.get("epsEstimate")),
                revenue_estimate=_optional_number(item.get("revenueEstimate")),
            )
            if symbol in events:
                if events[symbol] is not None and events[symbol].session != session:
                    # Withhold any ticker with contradictory reporting sessions.
                    events[symbol] = None
                    rejected += 1
            else:
                events[symbol] = event
    return tuple(x for x in events.values() if x is not None), rejected


def reporting_week(now=None):
    """One automatic Monday–Sunday window, rolling at Friday 16:00 ET."""
    now = datetime.now(ET) if now is None else now
    if now.tzinfo is None:
        raise ValueError("An aware datetime is required")
    local = now.astimezone(ET)
    monday = local.date() - timedelta(days=local.weekday())
    if local.weekday() > 4 or (local.weekday() == 4 and local.hour >= 16):
        monday += timedelta(days=7)
    return monday


def cache_expiry(fetched, monday):
    """A snapshot lives at most seven days, and never beyond week rollover.

    Construct Friday's local wall-clock cutoff rather than adding UTC seconds
    across a DST transition. Previous-week payloads are never reused for a new week.
    """
    friday = monday + timedelta(days=4)
    rollover = datetime(friday.year, friday.month, friday.day, 16, tzinfo=ET).timestamp()
    return min(fetched + CACHE_SECONDS, rollover)


class EarningsAPIService:
    """SQLite shared lease, durable precharged budget, and expiring display cache.

    Configure a persistent local volume shared by all processes on one host.
    Missing/unwritable storage fails closed rather than spending untracked quota.
    """
    def __init__(self, cache_path=None):
        self.cache_path = cache_path

    def load_week(self, api_key, monday=None, *, client=None, now=None, cache_path=None):
        now = time.time() if now is None else now
        selected = reporting_week(datetime.fromtimestamp(now, UTC))
        if monday is not None and monday != selected:
            return WeekResult(error="Only the automatic reporting week is available.")
        monday = selected
        if not api_key or not api_key.strip():
            return WeekResult(error="Configure EARNINGSAPI_API_KEY on the server.")
        path = self.cache_path or cache_path or os.environ.get("EARNINGSAPI_CACHE_PATH")
        if not path:
            return WeekResult(error="Persistent earnings cache is not configured; showing issuer announcements.")
        try:
            return self._load(path, api_key, monday, client, now)
        except (OSError, sqlite3.Error, ValueError, TypeError, KeyError):
            return WeekResult(error="Earnings cache unavailable; no untracked requests will be made.")

    def _load(self, path, api_key, monday, client, now):
        # The directory must be provisioned privately by the operator. No secrets
        # or credential hashes are stored; key rotation cannot reset the budget.
        with sqlite3.connect(Path(path), timeout=2) as db:
            db.execute("CREATE TABLE IF NOT EXISTS weeks (week TEXT PRIMARY KEY, next_attempt REAL, payload TEXT, fetched REAL)")
            db.execute("CREATE TABLE IF NOT EXISTS budget (month TEXT PRIMARY KEY, calls INTEGER)")
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE weeks SET payload=NULL, fetched=NULL WHERE fetched <= ? OR week <> ?",
                       (now-CACHE_SECONDS, monday.isoformat()))
            row = db.execute("SELECT next_attempt, payload, fetched FROM weeks WHERE week=?", (monday.isoformat(),)).fetchone()
            if row and row[1] and row[2] is not None and now < cache_expiry(row[2], monday):
                saved = json.loads(row[1])
                events = tuple(EarningsEvent(**dict(e, day=date.fromisoformat(e["day"]))) for e in saved["events"])
                return WeekResult(events=events, retrieved_at=row[2], rejected=saved["rejected"],
                                  cache_expires_at=cache_expiry(row[2], monday))
            if row and now < row[0]:
                return WeekResult(error="Calendar refresh pending or unavailable; next automatic attempt after " + datetime.fromtimestamp(row[0], ET).strftime("%b %d, %Y %I:%M %p ET") + ".")
            month = datetime.fromtimestamp(now, ET).strftime("%Y-%m")
            db.execute("INSERT OR IGNORE INTO budget VALUES (?, 0)", (month,))
            used = db.execute("SELECT calls FROM budget WHERE month=?", (month,)).fetchone()[0]
            if used + WEEK_REQUESTS > MONTHLY_REQUEST_BUDGET:
                return WeekResult(error="Calendar monthly request budget reached; showing issuer announcements.")
            # Charge the entire batch before HTTP. Crash, timeout, malformed data,
            # and failed responses cannot reset the retry cooldown or monthly cap.
            db.execute("UPDATE budget SET calls=calls+? WHERE month=?", (WEEK_REQUESTS, month))
            db.execute("INSERT OR REPLACE INTO weeks VALUES (?, ?, NULL, NULL)", (monday.isoformat(), now+RETRY_SECONDS))
            db.execute("DELETE FROM weeks WHERE week < ?", ((monday-timedelta(days=14)).isoformat(),))
            db.execute("DELETE FROM budget WHERE month < ?", (month,))
            db.commit()
            def fetch(http):
                events, rejected = [], 0
                for offset in range(WEEK_REQUESTS):
                    day = monday + timedelta(days=offset)
                    response = http.get(API_URL, params={"date": day.isoformat(), "apikey": api_key}, timeout=12.0, follow_redirects=False)
                    if response.status_code != 200:
                        raise ValueError("Unavailable provider")
                    found, invalid = normalize_day(response.json(), day)
                    events.extend(found)
                    rejected += invalid
                return WeekResult(events=tuple(sorted(events, key=lambda e: (e.day, e.session, e.symbol))), retrieved_at=now, rejected=rejected,
                                  cache_expires_at=cache_expiry(now, monday))
            try:
                if client is None:
                    with httpx.Client() as http:
                        result = fetch(http)
                else:
                    result = fetch(client)
            except (httpx.HTTPError, ValueError):
                return WeekResult(error="EarningsAPI unavailable. Automatic retry is paused for 24 hours; showing issuer announcements.")
            from dataclasses import asdict
            payload = json.dumps({"events": [dict(asdict(e), day=e.day.isoformat()) for e in result.events], "rejected": result.rejected})
            db.execute("UPDATE weeks SET payload=?, fetched=? WHERE week=?", (payload, now, monday.isoformat()))
            return result


earnings_api_service = EarningsAPIService()
