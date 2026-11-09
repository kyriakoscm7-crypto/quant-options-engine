"""Source reconciliation must correct dates without extra HTTP or duplicates."""
from datetime import date, timedelta

from app.intelligence.earnings_api_provider import EarningsEvent
from app.intelligence.earnings_ranking import (
    FEATURED_MAJOR_SYMBOLS,
    order_featured_events,
)
from app.intelligence.issuer_calendar import RELEASE_REVIEWED as REVIEWED
from app.intelligence.issuer_calendar import reconcile_provider_events

START = date(2026, 11, 9)


def test_reviewed_release_dates_replace_conflicts_and_fill_known_omissions():
    original = (EarningsEvent('CSCO', 'Cisco', date(2026, 11, 11), 'After market'),
                EarningsEvent('CSCO', 'Cisco', date(2026, 11, 12), 'Before market'),
                EarningsEvent('TDG', 'TransDigm', date(2026, 11, 11), 'Before market'),
                EarningsEvent('OTHER', 'Other', START, 'Time not supplied'))
    events, sources, conflicts = reconcile_provider_events(original, START, REVIEWED)
    by_symbol = {e.symbol: e for e in events}
    assert by_symbol['CSCO'].day == date(2026, 11, 12)
    assert by_symbol['CSCO'].session == 'After market'
    assert by_symbol['TDG'].day == date(2026, 11, 10)
    assert by_symbol['TTD'].day == START  # actual issuer release, not fabricated padding
    assert by_symbol['OTHER'] == original[-1]
    assert conflicts == 2
    assert len(events) == len(by_symbol)
    assert len(original) == 4 and original[0].day == date(2026, 11, 11)
    assert all(fact['source'].startswith('https://') for fact in sources.values())
    assert reconcile_provider_events(events, START, REVIEWED)[0] == events


def test_call_only_sources_cannot_override_release_or_create_events():
    event = EarningsEvent('CRWV', 'CoreWeave', START, 'After market')
    rows, sources, conflicts = reconcile_provider_events((event,), START, REVIEWED,
        [dict(symbol='CRWV', company='CoreWeave', day='2026-11-10', call='5 p.m. ET',
              source='https://example.com/issuer')])
    assert rows == (event,) and not sources and conflicts == 0


def test_announcements_expire_and_never_leak_between_reporting_weeks():
    assert reconcile_provider_events((), START, REVIEWED - timedelta(days=1)) == ((), {}, 0)
    assert reconcile_provider_events((), START, REVIEWED + timedelta(days=31)) == ((), {}, 0)
    assert reconcile_provider_events((), START + timedelta(days=7), REVIEWED) == ((), {}, 0)


def test_major_weekly_companies_have_explicit_editorial_priority():
    symbols = ['FERG', 'TTWO', 'TDG', 'AMAT', 'CSCO']
    assert set(symbols) <= FEATURED_MAJOR_SYMBOLS
    events = [EarningsEvent(s, s, START, 'Time not supplied') for s in symbols]
    ranked, _ = order_featured_events(events)
    assert [e.symbol for e in ranked] == ['CSCO', 'AMAT', 'TDG', 'FERG', 'TTWO']
