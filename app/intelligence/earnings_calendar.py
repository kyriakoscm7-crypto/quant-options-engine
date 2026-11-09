"""Finnhub's documented US calendar. No scraping, inferred confirmation or disk retention."""
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from threading import RLock

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

    def load(self, config, start, end, **kwargs):
        """Public build: credentials and scope flags never enable this provider.

        Keep the compatibility entry point for existing callers, but discard any
        previous in-memory results before returning. No HTTP client is created.
        """
        self.clear()
        return CalendarResult(
            error="Earnings calendar disabled in the public build. "
            "No provider data or derived results are available."
        )

    def clear(self):
        with self._lock:
            self._cache.clear()


calendar_service = CalendarService()
