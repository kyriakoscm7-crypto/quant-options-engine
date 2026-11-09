from dataclasses import replace
from datetime import date, timedelta
from types import SimpleNamespace

from app.intelligence.earnings_api_provider import EarningsEvent
from app.intelligence.earnings_ranking import CapObservation, order_events, select_page

TODAY = date(2026, 11, 9)
EVENTS = tuple(EarningsEvent(f'T{i:04}', f'Company {i}', TODAY + timedelta(days=i % 5), 'Before market') for i in range(1270))


def test_full_search_and_paging():
    ordered, label = order_events(EVENTS, TODAY)
    assert 'unavailable' in label
    assert list(ordered) == sorted(EVENTS, key=lambda e: (e.day, e.symbol))
    assert len(select_page(ordered)[0]) == 10
    assert len(select_page(ordered, limit=20)[0]) == 20
    assert select_page(ordered, 'T1269')[0][0].symbol == 'T1269'
    assert select_page(ordered, day=TODAY)[1] == 254
    assert select_page(ordered, 'absent') == ((), 0)


def test_complete_cap_order_and_fail_closed():
    events = EVENTS[:3]
    caps = {e.symbol: CapObservation((i + 1) * 1e9, TODAY, 'Synthetic licensed fixture', 'https://example.com', True) for i, e in enumerate(events)}
    adapter = SimpleNamespace(observations=lambda symbols: caps)
    ordered, label = order_events(events, TODAY, adapter)
    assert [e.symbol for e in ordered] == ['T0002', 'T0001', 'T0000']
    assert 'Largest market cap first' in label
    original = caps['T0000']
    for change in [dict(usd=float('nan')), dict(usd=-1), dict(usd=True), dict(display_authorized=False), dict(as_of=TODAY-timedelta(days=5)), dict(as_of=TODAY+timedelta(days=1)), dict(as_of=TODAY-timedelta(days=1)), dict(source_url='http://example.com'), dict(source='')]:
        caps['T0000'] = replace(original, **change)
        assert order_events(events, TODAY, adapter) == order_events(events, TODAY)
    del caps['T0000']
    assert order_events(events, TODAY, adapter) == order_events(events, TODAY)
    broken = SimpleNamespace(observations=lambda symbols: 1/0)
    assert order_events(events, TODAY, broken) == order_events(events, TODAY)


def test_featured_cross_week_order_preserves_only_provider_events():
    from app.intelligence.earnings_ranking import order_featured_events
    events = (EarningsEvent('ZZTEST', 'Synthetic', TODAY, 'Before market'),
              EarningsEvent('NVDA', 'Synthetic Nvidia', TODAY + timedelta(days=4), 'After market'),
              EarningsEvent('AAPL', 'Synthetic Apple', TODAY + timedelta(days=4), 'Before market'),
              EarningsEvent('AATEST', 'Synthetic', TODAY, 'Time not supplied'))
    ordered, label = order_featured_events(reversed(events))
    assert [e.symbol for e in ordered] == ['AAPL', 'NVDA', 'AATEST', 'ZZTEST']
    assert set(ordered) == set(events) and len(ordered) == len(set(ordered))
    assert 'Editorial priority' in label and 'not market-cap' in label
    assert order_featured_events(ordered)[0] == ordered
    assert select_page(ordered, 'synthetic apple')[0] == (events[2],)
    assert select_page(ordered, day=TODAY)[0] == (events[3], events[0])
    assert select_page(ordered, query='NVDA', day=TODAY) == ((), 0)


def test_featured_normalization_preserves_listing_and_share_class():
    from app.intelligence.earnings_ranking import (
        normalize_featured_symbol,
        order_featured_events,
    )
    assert normalize_featured_symbol(' brk-b ') == 'BRK.B'
    symbols = ['AAPL.L', 'BRK.A', 'ZZTEST', ' brk-b ', ' aapl ']
    events = tuple(EarningsEvent(s, s, TODAY, 'Time not supplied') for s in symbols)
    ordered, _ = order_featured_events(events)
    assert {e.symbol for e in ordered[:2]} == {' brk-b ', ' aapl '}
    assert set(ordered) == set(events)  # no provider symbol rewritten


def test_featured_full_universe_paging_and_clear_fallback():
    from app.intelligence.earnings_ranking import order_featured_events
    ordered, label = order_featured_events(EVENTS)
    assert 'No featured major companies' in label and 'Date, then ticker' in label
    assert order_featured_events(())[0] == ()
    assert len(ordered) == 1270
    assert select_page(ordered, 'T1269')[1] == 1
    assert select_page(ordered, day=TODAY)[1] == 254
    for limit in range(10, 1280, 10):
        rows, count = select_page(ordered, limit=limit)
        assert count == 1270 and len(rows) == min(limit, 1270)
        assert len(rows) == len(set(rows))


def test_editorial_priority_beats_earlier_reporting_day():
    from app.intelligence.earnings_ranking import order_featured_events
    events = (EarningsEvent('AAPL', 'Apple', TODAY + timedelta(days=4), 'After market'),
              EarningsEvent('AMD', 'AMD', TODAY, 'Before market'),
              EarningsEvent('MSFT', 'Microsoft', TODAY + timedelta(days=2), 'After market'))
    ordered, _ = order_featured_events(events)
    assert [e.symbol for e in ordered] == ['AAPL', 'MSFT', 'AMD']
    assert select_page(ordered, day=TODAY)[0] == (events[1],)


def test_calendar_selection_and_pagination_state():
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'qa/earnings_preview.py')).run()
    assert not app.exception
    assert app.radio[0].value == 'Top this week'
    assert app.session_state['earnings_limit'] == 10
    app.radio[0].set_value('Wed').run()
    assert app.session_state['earnings_selection'] == ('2026-11-09', 'Wed')
    app.run()
    assert app.radio[0].value == 'Wed'
    app.session_state['earnings_limit'] = 30
    app.radio[0].set_value('All week').run()
    assert app.session_state['earnings_limit'] == 10
    assert app.radio[0].value == 'All week'
    assert not app.exception
