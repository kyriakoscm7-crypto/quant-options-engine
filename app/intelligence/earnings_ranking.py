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


# Editorial membership only, version 1 (2026-11-07). Alphabetical, deliberately
# broad, manually maintained; neither a cap dataset nor a ranked size claim.
# Exact listing matches only: do not strip exchange suffixes or alias share classes.
FEATURED_MAJOR_SYMBOLS = frozenset({
    'AAPL', 'ABBV', 'ABNB', 'ABT', 'ADBE', 'ADI', 'ADP', 'ADSK', 'AEP', 'AFL',
    'AIG', 'AMAT', 'AMD', 'AMGN', 'AMT', 'AMZN', 'ANET', 'AON', 'APD', 'APO',
    'AVGO', 'AXP', 'AZN', 'BA', 'BABA', 'BAC', 'BDX', 'BIDU', 'BIIB', 'BK',
    'BKNG', 'BLK', 'BMY', 'BP', 'BRK.B', 'BSX', 'BX', 'C', 'CAT', 'CB',
    'CCI', 'CCL', 'CDNS', 'CEG', 'CHD', 'CI', 'CL', 'CMCSA', 'CME', 'CMG',
    'COF', 'COP', 'COST', 'CRM', 'CRWD', 'CSCO', 'CSX', 'CTAS', 'CVS', 'CVX',
    'D', 'DAL', 'DASH', 'DD', 'DE', 'DECK', 'DELL', 'DEO', 'DHR', 'DIS',
    'DLR', 'DOW', 'DUK', 'DVN', 'EA', 'EBAY', 'ECL', 'EL', 'EMR', 'ENPH',
    'EOG', 'EQIX', 'ETN', 'EXC', 'F', 'FDX', 'FI', 'FIS', 'FSLR', 'FTNT',
    'GD', 'GE', 'GEHC', 'GILD', 'GIS', 'GM', 'GOOG', 'GOOGL', 'GS', 'GSK',
    'HAL', 'HCA', 'HD', 'HLT', 'HON', 'HOOD', 'HPQ', 'HSY', 'HUM', 'IBM',
    'ICE', 'INTC', 'INTU', 'ISRG', 'ITW', 'JCI', 'JD', 'JNJ', 'JPM', 'KDP',
    'KHC', 'KKR', 'KLAC', 'KMB', 'KO', 'KR', 'LLY', 'LMT', 'LOW', 'LRCX',
    'LULU', 'LVS', 'MA', 'MAR', 'MCD', 'MCHP', 'MCK', 'MDB', 'MDLZ', 'MDT',
    'MELI', 'MET', 'META', 'MMM', 'MO', 'MPC', 'MRK', 'MRNA', 'MRVL', 'MS',
    'MSFT', 'MSI', 'MU', 'NEE', 'NEM', 'NET', 'NFLX', 'NKE', 'NOC', 'NOW',
    'NSC', 'NTES', 'NVDA', 'NVO', 'NXPI', 'O', 'ODFL', 'OKTA', 'ORCL', 'ORLY',
    'OXY', 'PANW', 'PAYX', 'PBR', 'PCAR', 'PDD', 'PEP', 'PFE', 'PG', 'PGR',
    'PLD', 'PLTR', 'PM', 'PNC', 'PSA', 'PSX', 'PYPL', 'QCOM', 'RACE', 'RCL',
    'REGN', 'RIO', 'RIVN', 'ROKU', 'ROST', 'RTX', 'SBUX', 'SCHW', 'SE', 'SHOP',
    'SLB', 'SMCI', 'SNAP', 'SNOW', 'SNPS', 'SO', 'SOFI', 'SONY', 'SPG', 'SPGI',
    'SPOT', 'SRE', 'STLA', 'STT', 'STZ', 'SU', 'SYK', 'SYY', 'T', 'TGT',
    'TJX', 'TM', 'TMO', 'TMUS', 'TOL', 'TRV', 'TSLA', 'TSM', 'TT', 'TTD',
    'TXN', 'UAL', 'UBER', 'UBS', 'UL', 'UNH', 'UNP', 'UPS', 'USB', 'V',
    'VLO', 'VRTX', 'VZ', 'WBA', 'WBD', 'WDAY', 'WDC', 'WEC', 'WFC', 'WM',
    'WMT', 'XEL', 'XOM', 'XYZ', 'YUM', 'ZM', 'ZS', 'ZTS',
})


def normalize_featured_symbol(symbol):
    """Match provider whitespace/case and dot/hyphen share-class notation only.

    Never remove a listing suffix (e.g. AAPL.L) or map a different share class.
    The original provider event and Research symbol always remain unchanged.
    """
    return symbol.strip().upper().replace('-', '.')


def order_featured_events(events):
    """Partition verified input events; add no events, values or provider requests.

    Sort each partition by day/ticker across the full week before pagination.
    normalize_day already deduplicates and withholds contradictory sessions.
    """
    events = tuple(events)
    def featured(event):
        return normalize_featured_symbol(event.symbol) in FEATURED_MAJOR_SYMBOLS
    ordered = tuple(sorted(events, key=lambda e: (not featured(e), e.day, e.symbol)))
    if any(featured(e) for e in events):
        return ordered, "Featured major companies · Curated list, not market-cap ranking"
    return ordered, "No featured major companies in this week's provider events · Date, then ticker"


def select_page(events, query='', day=None, limit=10):
    query = query.strip().casefold()
    matches = tuple(e for e in events if (day is None or e.day == day)
                    and query in f'{e.symbol} {e.name}'.casefold())
    return matches[:max(10, limit)], len(matches)
