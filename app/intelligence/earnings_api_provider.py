"""EarningsAPI.com calendar adapter for the public earnings page.

The provider supplies date/session buckets, not company-confirmed schedules.
No third-party feed is exposed to clients; only the rendered calendar is displayed.
"""
from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass
from datetime import date, timedelta
from threading import RLock

import httpx

API_URL = "https://api.earningsapi.com/v2/calendar/earnings"
CACHE_SECONDS = 6 * 60 * 60
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
            if symbol in events and events[symbol].session != session:
                # Conflicting within-day sessions must not be silently resolved.
                events[symbol] = None
                rejected += 1
            elif symbol not in events:
                events[symbol] = event
    return tuple(x for x in events.values() if x is not None), rejected


class EarningsAPIService:
    """In-process six-hour week cache; no storage of key or raw provider payload."""
    def __init__(self):
        self._lock = RLock()
        self._cache = {}

    def load_week(self, api_key: str, monday: date, *, client=None, now=None):
        if not api_key or not api_key.strip():
            return WeekResult(error="Configure EARNINGSAPI_API_KEY on the server.")
        if monday.weekday() != 0:
            return WeekResult(error="Calendar start must be a Monday.")
        now = time.time() if now is None else now
        identity = (hashlib.sha256(api_key.encode()).hexdigest(), monday)
        with self._lock:
            entry = self._cache.get(identity)
            if entry and now - entry[0] < CACHE_SECONDS:
                return entry[1]

            def fetch(http):
                events = []
                rejected = 0
                for offset in range(7):
                    day = monday + timedelta(days=offset)
                    response = http.get(
                        API_URL,
                        params={"date": day.isoformat(), "apikey": api_key},
                        timeout=12.0,
                        follow_redirects=False,
                    )
                    if response.status_code == 429:
                        raise RuntimeError("EarningsAPI request limit reached; try later.")
                    if response.status_code in (401, 403):
                        raise RuntimeError("EarningsAPI key was rejected or lacks calendar access.")
                    if response.status_code != 200:
                        raise RuntimeError("EarningsAPI calendar is temporarily unavailable.")
                    found, invalid = normalize_day(response.json(), day)
                    events.extend(found)
                    rejected += invalid
                return WeekResult(
                    events=tuple(sorted(events, key=lambda e: (e.day, e.session, e.symbol))),
                    retrieved_at=now,
                    rejected=rejected,
                )

            try:
                if client is None:
                    with httpx.Client() as http:
                        result = fetch(http)
                else:
                    result = fetch(client)
            except (httpx.HTTPError, ValueError, RuntimeError) as exc:
                # Never expose URLs, response bodies, HTTP errors or key in UI.
                if isinstance(exc, RuntimeError):
                    message = str(exc)
                else:
                    message = "Unable to verify the EarningsAPI response right now."
                result = WeekResult(error=message)
            # Cache only a successful, complete week. Do not treat partial data as complete.
            if not result.error:
                self._cache[identity] = (now, result)
                if len(self._cache) > 20:
                    self._cache.pop(next(iter(self._cache)))
            return result


earnings_api_service = EarningsAPIService()
