from datetime import date
from urllib.parse import urlsplit

from app.intelligence.issuer_calendar import EVENTS, REVIEWED, select_events


def test_windows_search_and_expiry():
    assert not select_events(REVIEWED, "This week")
    assert [e['symbol'] for e in select_events(REVIEWED, "Next week")] == ['FERG', 'TTD', 'TTWO', 'CRWV', 'TDG', 'AMAT', 'CSCO']
    assert [e['symbol'] for e in select_events(REVIEWED, query='disney')] == ['DIS']
    assert not select_events(date(2026, 11, 10), query='TTD')
    assert not select_events(date(2026, 12, 7))
    assert not select_events(date(2026, 11, 5))


def test_provenance_and_no_inferred_release_times():
    assert len({e['symbol'] for e in EVENTS}) == len(EVENTS)
    assert list(EVENTS) == sorted(EVENTS, key=lambda e: (e['day'], e['symbol']))
    for event in EVENTS:
        assert urlsplit(event['source']).scheme == 'https'
        assert date.fromisoformat(event['day']) >= REVIEWED
        if not event.get('release_session'):
            assert event['release'] == 'Release timing not specified'
