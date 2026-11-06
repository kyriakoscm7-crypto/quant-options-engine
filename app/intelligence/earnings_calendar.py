"""Finnhub's documented US calendar. No scraping, inferred confirmation or disk retention."""
import re
import time
from contextlib import suppress
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from hashlib import sha256
from threading import RLock

import httpx

SOURCE = "https://finnhub.io/docs/api/earnings-calendar"
TTL = 900


@dataclass(frozen=True)
class CalendarConfig:
    api_key: str = field(default="", repr=False)
    use: str = ""  # personal_local or written_agreement


@dataclass(frozen=True)
class Event:
    symbol: str
    day: date
    session: str
    status: str = "Unconfirmed · provider does not distinguish estimated dates"
    source_updated_at: str = "Not supplied by provider"


@dataclass(frozen=True)
class CalendarResult:
    events: tuple[Event, ...] = ()
    retrieved_at: datetime | None = None
    error: str = ""
    rejected: int = 0


def normalize(payload, start, end):
    if not isinstance(payload, dict) or not isinstance(payload.get("earningsCalendar"), list):
        raise ValueError("Invalid calendar response")
    rows, rejected = {}, 0
    for item in payload["earningsCalendar"]:
        try:
            symbol = item["symbol"]
            if not isinstance(symbol, str) or not re.fullmatch(r"[A-Z][A-Z0-9.-]{0,14}", symbol):
                raise ValueError("Invalid symbol")
            day = date.fromisoformat(item["date"])
            if not start <= day <= end:
                continue
            session = {"bmo": "Before US market open", "amc": "After US market close", "dmh": "During US market hours"}.get(item.get("hour"), "Time not supplied")
            event = Event(symbol, day, session)
            key = (symbol, day)
            if key in rows and rows[key].session != session:
                event = Event(symbol, day, "Conflicting session information")
            rows[key] = event
        except (KeyError, TypeError, ValueError):
            rejected += 1
    # Different dates for one issuer in the requested week are not silently resolved.
    counts = {}
    for symbol, _ in rows:
        counts[symbol] = counts.get(symbol, 0) + 1
    return tuple(sorted((e for e in rows.values() if counts[e.symbol] == 1), key=lambda e: (e.day, e.symbol))), rejected + sum(counts[e.symbol] > 1 for e in rows.values())


class CalendarService:
    def __init__(self):
        self._cache = {}
        self._lock = RLock()

    def load(self, config, start, end, *, client=None, clock=time.monotonic, sleep=time.sleep):
        if config.use not in {"personal_local", "written_agreement"}:
            self.clear()
            return CalendarResult(error="Choose authorized personal local use or a written provider agreement in server configuration. See docs/EARNINGS_CALENDAR.md.")
        if not config.api_key:
            self.clear()
            return CalendarResult(error="Finnhub API key is missing. Configure it locally in .streamlit/secrets.toml; never paste it into chat.")
        if not isinstance(start, date) or not isinstance(end, date) or not 0 <= (end - start).days <= 6:
            return CalendarResult(error="Choose a valid seven-day week.")
        key = (sha256(config.api_key.encode()).digest(), config.use, start, end)
        with self._lock:
            now = clock()
            self._cache = {k: v for k, v in self._cache.items() if v[0] > now}
            if key in self._cache:
                return self._cache[key][1]
            own = client is None
            client = client or httpx.Client(timeout=10, follow_redirects=False)
            try:
                result = self._fetch(client, config, start, end, sleep)
            finally:
                if own:
                    client.close()
            # Short negative cache prevents rerun/request storms. Never serve expired data.
            self._cache[key] = (clock() + (TTL if not result.error else 30), result)
            while len(self._cache) > 64:
                self._cache.pop(next(iter(self._cache)))
            return result

    def _fetch(self, client, config, start, end, sleep):
        for attempt in range(3):
            try:
                with client.stream("GET", "https://finnhub.io/api/v1/calendar/earnings", params={"from": start.isoformat(), "to": end.isoformat(), "international": "false"}, headers={"X-Finnhub-Token": config.api_key}) as streamed:
                    body = bytearray()
                    for chunk in streamed.iter_bytes():
                        body.extend(chunk)
                        if len(body) > 2_000_000:
                            return CalendarResult(error="Finnhub response exceeded the calendar size limit; no dates shown.")
                    response = httpx.Response(streamed.status_code, headers=streamed.headers, content=bytes(body))
                if response.status_code in {401, 403}:
                    return CalendarResult(error="Finnhub rejected access. Check the local key and calendar entitlement in your provider account.")
                if response.status_code == 429 or response.status_code >= 500:
                    if attempt < 2:
                        delay = 2 ** attempt
                        if response.status_code == 429:
                            with suppress(ValueError):
                                delay = max(delay, float(response.headers.get("Retry-After", delay)))
                            if delay > 5:
                                return CalendarResult(error="Finnhub rate limit reached. Try again later.")
                        sleep(delay)
                        continue
                    return CalendarResult(error="Finnhub is rate limited or temporarily unavailable. Try again later.")
                if response.status_code != 200:
                    return CalendarResult(error="Finnhub calendar request failed. Check provider access; no dates substituted.")
                events, rejected = normalize(response.json(), start, end)
                if rejected and not events:
                    return CalendarResult(error="Calendar response contained only invalid or conflicting events; no dates shown.", rejected=rejected)
                return CalendarResult(events, datetime.now(UTC), rejected=rejected)
            except httpx.TransportError:
                if attempt < 2:
                    sleep(2 ** attempt)
                    continue
                return CalendarResult(error="Cannot reach Finnhub. Check connectivity and try again.")
            except (ValueError, TypeError):
                return CalendarResult(error="Finnhub returned an invalid calendar response; no dates substituted.")

    def clear(self):
        with self._lock:
            self._cache.clear()


calendar_service = CalendarService()
