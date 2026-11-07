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
