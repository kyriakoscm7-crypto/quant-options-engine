"""Offline tests; fixtures are synthetic and never presented as real earnings."""
from datetime import date, timedelta

import httpx

from app.intelligence.earnings_api_provider import (
    EarningsAPIService,
    normalize_day,
)

MONDAY = date(2026, 11, 9)


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


def test_week_cache_fetches_seven_days_once_and_never_logs_key():
    calls = []

    def respond(request):
        calls.append(request)
        day = request.url.params["date"]
        assert request.url.params["apikey"] == "private-key-for-test"
        return httpx.Response(200, json=fixture(day))

    service = EarningsAPIService()
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        result = service.load_week("private-key-for-test", MONDAY, client=client, now=100.0)
        again = service.load_week("private-key-for-test", MONDAY, client=client, now=101.0)
    assert not result.error and result.retrieved_at == 100.0
    assert len(calls) == 7
    assert len(result.events) == 14
    assert again == result
    assert "private-key-for-test" not in repr(result)
    assert all(MONDAY <= e.day <= MONDAY + timedelta(days=6) for e in result.events)


def test_partial_week_failure_not_cached_and_key_not_exposed():
    count = 0

    def respond(request):
        nonlocal count
        count += 1
        if count == 3:
            return httpx.Response(429)
        return httpx.Response(200, json=fixture(request.url.params["date"]))

    service = EarningsAPIService()
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        result = service.load_week("secret-value", MONDAY, client=client, now=1.0)
    assert result.error and not result.events
    assert not service._cache
    assert "secret-value" not in result.error


def test_missing_key_never_calls_provider():
    service = EarningsAPIService()
    assert "Configure" in service.load_week("", MONDAY).error
