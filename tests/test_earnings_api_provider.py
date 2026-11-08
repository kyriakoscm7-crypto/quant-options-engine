"""Offline tests; fixtures are synthetic and never presented as real earnings."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
import pytest

from app.intelligence.earnings_api_provider import (
    EarningsAPIService,
    normalize_day,
)

MONDAY = date(2026, 11, 9)
NOW = datetime(2026, 11, 9, 12, tzinfo=ZoneInfo("America/New_York")).timestamp()


def fixture(day):
    return {
        "date": day,
        "pre": [{"symbol": "TEST", "name": "Test Company", "epsEstimate": 1.25}],
        "after": [{"symbol": "EXAM", "name": "Example Corporation"}],
        "notSupplied": [],
    }


def test_valid_events_and_missing_estimates():
    events, rejected = normalize_day(fixture("2026-11-09"), MONDAY)
    assert not rejected and len(events) == 2
    assert events[0].session == "Before market"
    assert events[0].eps_estimate == 1.25
    assert events[1].eps_estimate is None
    assert events[1].session == "After market"


def test_invalid_and_conflicting_events_are_not_displayed():
    data = fixture("2026-11-09")
    data["after"].append({"symbol": "TEST", "name": "Test Company"})
    data["pre"].append({"symbol": "<bad>"})
    data["pre"].append({"symbol": "NAN", "epsEstimate": "NaN"})
    events, rejected = normalize_day(data, MONDAY)
    assert rejected == 2
    assert {event.symbol for event in events} == {"EXAM", "NAN"}
    assert next(e for e in events if e.symbol == "NAN").eps_estimate is None


def test_bad_shape_fails_without_inventing_earnings():
    import pytest

    with pytest.raises(ValueError):
        normalize_day({"date": "2026-11-10", "pre": [], "after": [], "notSupplied": []}, MONDAY)
    with pytest.raises(ValueError):
        normalize_day({"date": "2026-11-09", "pre": []}, MONDAY)


def test_week_cache_fetches_seven_days_once_and_never_logs_key(tmp_path):
    calls = []

    def respond(request):
        calls.append(request)
        day = request.url.params["date"]
        assert request.url.params["apikey"] == "private-key-for-test"
        return httpx.Response(200, json=fixture(day))

    service = EarningsAPIService(tmp_path / "cache.sqlite")
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        result = service.load_week("private-key-for-test", MONDAY, client=client, now=NOW)
        again = service.load_week("private-key-for-test", MONDAY, client=client, now=NOW+1)
    assert not result.error and result.retrieved_at == NOW
    assert len(calls) == 7
    assert len(result.events) == 14
    assert again == result
    assert "private-key-for-test" not in repr(result)
    assert all(MONDAY <= e.day <= MONDAY + timedelta(days=6) for e in result.events)


def test_partial_week_failure_not_cached_and_key_not_exposed(tmp_path):
    count = 0

    def respond(request):
        nonlocal count
        count += 1
        if count == 3:
            return httpx.Response(429)
        return httpx.Response(200, json=fixture(request.url.params["date"]))

    service = EarningsAPIService(tmp_path / "cache.sqlite")
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        result = service.load_week("secret-value", MONDAY, client=client, now=NOW)
    assert result.error and not result.events
    again = service.load_week("rotated-key", MONDAY, client=client, now=NOW+1)
    assert again.error and count == 3
    assert "secret-value" not in result.error


def test_missing_key_never_calls_provider(tmp_path):
    service = EarningsAPIService(tmp_path / "cache.sqlite")
    assert "Configure" in service.load_week("", MONDAY).error


@pytest.mark.parametrize("instant,expected", [
    ("2026-11-02T00:00:00-05:00", "2026-11-02"),
    ("2026-11-03T12:00:00-05:00", "2026-11-02"),
    ("2026-11-04T12:00:00-05:00", "2026-11-02"),
    ("2026-11-05T12:00:00-05:00", "2026-11-02"),
    ("2026-11-06T15:59:59-05:00", "2026-11-02"),
    ("2026-11-06T21:00:00+00:00", "2026-11-09"),
    ("2026-11-07T12:00:00-05:00", "2026-11-09"),
    ("2026-11-08T12:00:00-05:00", "2026-11-09"),
    ("2027-01-01T16:00:00-05:00", "2027-01-04"),
    ("2026-03-08T03:00:00-04:00", "2026-03-09"),
    ("2026-03-13T20:00:00+00:00", "2026-03-16"),
    ("2026-11-01T01:30:00-04:00", "2026-11-02"),
    ("2026-11-01T01:30:00-05:00", "2026-11-02"),
])
def test_automatic_week(instant, expected):
    from app.intelligence.earnings_api_provider import reporting_week
    assert reporting_week(datetime.fromisoformat(instant)).isoformat() == expected


def test_durable_cache_and_concurrency_budget(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Lock
    path = tmp_path / "shared.sqlite"
    calls = []
    lock = Lock()
    def respond(request):
        with lock:
            calls.append(request)
        return httpx.Response(200, json=fixture(request.url.params["date"]))
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        def load(_):
            return EarningsAPIService(path).load_week("key", client=client, now=NOW)
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(load, range(16)))
        assert any(not r.error for r in results)
        assert len(calls) == 7
        assert not load(0).error
        EarningsAPIService(path).load_week("rotated", client=client, now=NOW+86400)
        assert len(calls) == 7
    assert b"rotated" not in path.read_bytes()


def test_arbitrary_week_and_unconfigured_storage_do_not_fetch(monkeypatch):
    monkeypatch.delenv("EARNINGSAPI_CACHE_PATH", raising=False)
    service = EarningsAPIService()
    assert service.load_week("key", MONDAY+timedelta(days=7), now=NOW).error
    assert service.load_week("key", now=NOW).error


def test_monthly_budget_and_failed_restart_are_durable(tmp_path):
    import sqlite3
    path = tmp_path / 'budget.sqlite'
    calls = []
    def unavailable(request):
        calls.append(request)
        return httpx.Response(503)
    with httpx.Client(transport=httpx.MockTransport(unavailable)) as client:
        assert EarningsAPIService(path).load_week('key', client=client, now=NOW).error
        assert EarningsAPIService(path).load_week('new-key', client=client, now=NOW+100).error
        assert len(calls) == 1
        with sqlite3.connect(path) as db:
            db.execute("UPDATE budget SET calls=245")
        assert EarningsAPIService(path).load_week('key', client=client, now=NOW+86400).error
        assert len(calls) == 1


def test_featured_interactions_are_quota_neutral_and_deduplicated(tmp_path):
    from app.intelligence.earnings_ranking import order_featured_events, select_page
    calls = []
    def respond(request):
        calls.append(request)
        payload = fixture(request.url.params['date'])
        # Case/whitespace duplicates normalize to one verified listing per day.
        payload['pre'] += [{'symbol': ' aapl ', 'name': 'Synthetic Apple'},
                           {'symbol': 'AAPL', 'name': 'Synthetic Apple'}]
        return httpx.Response(200, json=payload)
    service = EarningsAPIService(tmp_path / 'featured.sqlite')
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        result = service.load_week('test', MONDAY, client=client, now=NOW)
        for query, day, limit in [('', None, 10), ('AAPL', None, 20),
                                  ('TEST', MONDAY, 30), ('absent', None, 40)]:
            cached = service.load_week('test', MONDAY, client=client, now=NOW+1)
            ordered, _ = order_featured_events(cached.events)
            select_page(ordered, query, day, limit)
        assert len(calls) == 7
    assert len(result.events) == 21
    assert len({(e.day, e.symbol) for e in ordered}) == len(ordered)
    assert all(e.symbol == 'AAPL' for e in ordered[:7])
    import sqlite3
    with sqlite3.connect(tmp_path / 'featured.sqlite') as db:
        assert db.execute('SELECT calls FROM budget').fetchone()[0] == 7


def test_thousands_of_visits_share_snapshot_across_restart_and_key_rotation(tmp_path):
    import sqlite3

    path = tmp_path / 'weekly.sqlite'
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(200, json=fixture(request.url.params['date']))

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        # Load the upcoming week on the preceding Saturday, then serve it through Friday.
        first_at = NOW - 2 * 86400
        first = EarningsAPIService(path).load_week('private-test', client=client, now=first_at)
        assert not first.error
        for visit in range(1000):
            cached = EarningsAPIService(path).load_week('rotated-test', client=client,
                                                       now=first_at + visit * 500)
            assert cached == first
        assert len(calls) == 7
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT calls FROM budget').fetchone()[0] == 7
    assert b'private-test' not in path.read_bytes()
    assert b'rotated-test' not in path.read_bytes()


def test_rollover_fetches_new_week_without_reusing_previous_snapshot(tmp_path):
    import sqlite3

    path = tmp_path / 'rollover.sqlite'
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(200, json=fixture(request.url.params['date']))

    cutoff = datetime(2026, 11, 13, 16, tzinfo=ZoneInfo('America/New_York')).timestamp()
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        service = EarningsAPIService(path)
        original = service.load_week('key', client=client, now=NOW)
        assert original.cache_expires_at == cutoff
        assert service.load_week('key', client=client, now=cutoff-1) == original
        newer = service.load_week('key', client=client, now=cutoff)
        assert not newer.error and len(calls) == 14
        assert all(e.day >= MONDAY + timedelta(days=7) for e in newer.events)
        with sqlite3.connect(path) as db:
            assert db.execute('SELECT payload FROM weeks WHERE week=?', (MONDAY.isoformat(),)).fetchone()[0] is None
            assert db.execute('SELECT calls FROM budget').fetchone()[0] == 14


def test_failed_batch_retries_after_day_not_week(tmp_path):
    path = tmp_path / 'retry.sqlite'
    calls = []

    def respond(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(503)
        return httpx.Response(200, json=fixture(request.url.params['date']))

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        service = EarningsAPIService(path)
        assert service.load_week('key', client=client, now=NOW).error
        assert service.load_week('key', client=client, now=NOW+86399).error
        assert len(calls) == 1
        assert not service.load_week('key', client=client, now=NOW+86400).error
        assert len(calls) == 8


def test_weekly_cache_expiry_ceiling_and_dst():
    from app.intelligence.earnings_api_provider import CACHE_SECONDS, cache_expiry

    assert CACHE_SECONDS == 7 * 86400
    # A malformed/older stored timestamp cannot prolong retention past seven days.
    assert cache_expiry(NOW - 10 * 86400, MONDAY) == NOW - 3 * 86400
    spring_monday = date(2026, 3, 9)
    saturday = datetime.fromisoformat('2026-03-07T16:00:00-05:00').timestamp()
    assert cache_expiry(saturday, spring_monday) == datetime.fromisoformat('2026-03-13T16:00:00-04:00').timestamp()


def test_seven_day_expired_payload_is_not_served(tmp_path):
    import sqlite3

    path = tmp_path / 'expired.sqlite'
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(200, json=fixture(request.url.params['date']))

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        service = EarningsAPIService(path)
        assert not service.load_week('key', client=client, now=NOW).error
        with sqlite3.connect(path) as db:
            db.execute('UPDATE weeks SET fetched=?', (NOW - 7*86400,))
        # Cache data is expired; the already-reserved failure cooldown still applies.
        assert service.load_week('key', client=client, now=NOW+1).error
        assert len(calls) == 7
        assert not service.load_week('key', client=client, now=NOW+86400).error
        assert len(calls) == 14


def test_cached_snapshot_available_even_when_monthly_budget_exhausted(tmp_path):
    import sqlite3

    path = tmp_path / 'exhausted.sqlite'
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(200, json=fixture(request.url.params['date']))

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        service = EarningsAPIService(path)
        result = service.load_week('key', client=client, now=NOW)
        with sqlite3.connect(path) as db:
            db.execute('UPDATE budget SET calls=250')
        assert service.load_week('key', client=client, now=NOW+86400) == result
        assert len(calls) == 7
        cutoff = datetime(2026, 11, 13, 16, tzinfo=ZoneInfo('America/New_York')).timestamp()
        assert 'budget reached' in service.load_week('key', client=client, now=cutoff).error
        assert len(calls) == 7


def test_server_supplied_cache_path_and_missing_parent_fail_closed(tmp_path):
    calls = []

    def respond(request):
        calls.append(request)
        return httpx.Response(200, json=fixture(request.url.params['date']))

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        service = EarningsAPIService()
        result = service.load_week('key', client=client, now=NOW,
                                   cache_path=tmp_path / 'private' / 'cache.sqlite')
        assert result.error and not calls
        result = service.load_week('key', client=client, now=NOW,
                                   cache_path=tmp_path / 'cache.sqlite')
        assert not result.error and len(calls) == 7
