"""Pure calendar ordering contract. No network, credentials or implied valuations."""
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date, timedelta
from math import isfinite
from typing import Protocol


@dataclass(frozen=True)
class CapObservation:
    usd: float
    as_of: date
    source: str
    source_url: str
    display_authorized: bool = False


class RankingAdapter(Protocol):
    """Implement only for a provider whose agreement covers this public display.

    Return comparable total issuer equity values in USD, resolving share classes
    and listing identity upstream. Never substitute exchange-local ticker matches.
    """

    def observations(self, symbols: set[str]) -> Mapping[str, CapObservation]: ...


def order_events(events, today, adapter: RankingAdapter | None = None):
    """Require complete, same-date, recent coverage; otherwise deterministic fallback.

    No partial-cap ordering: missing values cannot imply smaller companies.
    Adapter failures must not affect calendar availability or spend calendar quota.
    """
    events = tuple(events)
    fallback = tuple(sorted(events, key=lambda e: (e.day, e.symbol)))
    if not events or adapter is None:
        return fallback, "Date, then ticker · Market-cap ranking unavailable"
    try:
        caps = adapter.observations({e.symbol for e in events})
        selected = [caps[e.symbol] for e in events]
        if not all(c.display_authorized and c.source.strip()
                   and c.source_url.startswith('https://')
                   and not isinstance(c.usd, bool) and isfinite(c.usd) and c.usd > 0
                   and today - timedelta(days=4) <= c.as_of <= today for c in selected):
            return fallback, "Date, then ticker · Market-cap ranking unavailable"
        if len({c.as_of for c in selected}) != 1:
            return fallback, "Date, then ticker · Market-cap ranking unavailable"
        ordered = tuple(sorted(events, key=lambda e: (-caps[e.symbol].usd, e.day, e.symbol)))
        sources = ', '.join(sorted({c.source for c in selected}))
        return ordered, f"Largest market cap first · USD · {selected[0].as_of:%b %d, %Y} · {sources}"
    except Exception:
        return fallback, "Date, then ticker · Market-cap ranking unavailable"


def select_page(events, query='', day=None, limit=10):
    query = query.strip().casefold()
    matches = tuple(e for e in events if (day is None or e.day == day)
                    and query in f'{e.symbol} {e.name}'.casefold())
    return matches[:max(10, limit)], len(matches)
