"""Offline contract fixtures; these are not live events."""
from datetime import UTC, date

import httpx
import pytest
from streamlit.testing.v1 import AppTest

from app.intelligence.earnings_calendar import (
    CalendarConfig,
    CalendarResult,
    CalendarService,
    Event,
    normalize,
)

START, END = date(2026, 11, 2), date(2026, 11, 8)
CONFIG = CalendarConfig("test-secret", "personal_local")


def payload(**extra):
    return {"earningsCalendar": [{"symbol": "TEST", "date": "2026-11-06", "hour": "amc", **extra}]}


def test_normalization_and_no_inferred_confirmation():
    events, rejected = normalize(payload(), START, END)
    assert events[0].day == date(2026, 11, 6)
    assert events[0].status.startswith("Unconfirmed")
    assert events[0].source_updated_at == "Not supplied by provider"
    assert not rejected
    assert normalize(payload(date="2026-11-09"), START, END) == ((), 0)
    assert normalize(payload(symbol="<script>"), START, END) == ((), 1)
    assert normalize(payload(date="2026-02-30"), START, END) == ((), 1)
    with pytest.raises(ValueError):
        normalize({"error": "denied"}, START, END)


def test_duplicates_and_conflicting_dates():
    data = payload()
    data["earningsCalendar"] *= 2
    assert len(normalize(data, START, END)[0]) == 1
    data["earningsCalendar"].append({"symbol": "TEST", "date": "2026-11-05"})
    assert normalize(data, START, END) == ((), 2)


def test_cache_expiry_credentials_and_retry():
    calls, delays = [], []
    def handler(request):
        calls.append(request)
        assert request.headers["X-Finnhub-Token"] == "test-secret"
        assert "test-secret" not in str(request.url)
        assert request.url.params["from"] == "2026-11-02"
        return httpx.Response(503 if len(calls) == 1 else 200, json=payload())
    service = CalendarService()
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        first = service.load(CONFIG, START, END, client=client, clock=lambda: 0, sleep=delays.append)
        assert not first.error and first.retrieved_at.tzinfo
        assert delays == [1] and len(calls) == 2
        assert service.load(CONFIG, START, END, client=client, clock=lambda: 899) == first
        service.load(CONFIG, START, END, client=client, clock=lambda: 901)
        assert len(calls) == 3
        assert service.load(CalendarConfig(), START, END).error
        assert not service._cache
    assert "test-secret" not in repr(CONFIG)


@pytest.mark.parametrize('status', [401, 403, 429, 500, 302])
def test_errors_never_become_empty_success(status):
    count = []
    def handler(request):
        count.append(1)
        return httpx.Response(status, headers={"Retry-After": "60"}, json={"error": "test-secret"})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = CalendarService().load(CONFIG, START, END, client=client, sleep=lambda _: None)
    assert result.error and not result.events and result.retrieved_at is None
    assert "test-secret" not in result.error
    assert len(count) == (3 if status == 500 else 1)


def test_invalid_json_and_transport():
    for handler in [lambda r: httpx.Response(200, text="bad"), lambda r: httpx.Response(200, json={"error": "x"})]:
        with httpx.Client(transport=httpx.MockTransport(handler)) as client:
            assert CalendarService().load(CONFIG, START, END, client=client).error
    def broken(request):
        raise httpx.ReadTimeout("secret")
    with httpx.Client(transport=httpx.MockTransport(broken)) as client:
        assert CalendarService().load(CONFIG, START, END, client=client, sleep=lambda _: None).error


def test_week_cards_and_navigation(monkeypatch):
    from datetime import datetime

    from dashboard import earnings_week
    seen = []
    def load(config, start, end):
        seen.append((start, end))
        return CalendarResult((Event("TEST", start, "Time not supplied"),), datetime.now(UTC))
    monkeypatch.setattr(earnings_week.calendar_service, 'load', load)
    monkeypatch.setattr(earnings_week, 'open_research', lambda symbol: seen.append(symbol))
    app = AppTest.from_string("from dashboard.earnings_week import render_earnings_week\nrender_earnings_week()").run()
    # from_function must import its rendering module in the generated script.
    assert not app.exception
    next(b for b in app.button if b.label == 'Open TEST research →').click().run()
    assert 'TEST' in seen
    initial = next(x for x in seen if isinstance(x, tuple))
    next(b for b in app.button if b.label == 'Next week →').click().run()
    assert seen[-1][0] > initial[0]


def test_toronto_dst_date_only_week():
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from dashboard.earnings_week import week_bounds
    zone = ZoneInfo('America/Toronto')
    assert datetime(2026, 3, 8, 7, tzinfo=UTC).astimezone(zone).hour == 3
    assert week_bounds(date(2026, 3, 8)) == (date(2026, 3, 2), date(2026, 3, 8))
    assert week_bounds(date(2026, 11, 1)) == (date(2026, 10, 26), date(2026, 11, 1))
    event = normalize(payload(date='2026-11-02'), START, END)[0][0]
    assert event.day == START  # no fictitious UTC midnight shifted to Sunday


def test_research_uses_verified_identity_and_existing_route(monkeypatch):
    from types import SimpleNamespace

    from dashboard import discover_intelligence
    monkeypatch.setenv('QI_SEC_USER_AGENT', 'Research operator contact')
    monkeypatch.setattr(discover_intelligence, '_gateway', lambda agent: 'gateway')
    import app.intelligence.discover_service as service
    def deep_dive(gateway, symbol):
        assert gateway == 'gateway' and symbol == 'TEST'
        return {'company': SimpleNamespace(ticker='TEST')}
    monkeypatch.setattr(service, 'company_deep_dive', deep_dive)
    app = AppTest.from_string("from dashboard.earnings_week import open_research\nimport streamlit as st\nif not st.session_state.get('qi_earnings_origin'):\n    open_research('TEST')").run()
    assert not app.exception
    assert app.session_state['qi_detail'] == 'TEST'
    assert app.session_state['_navigation_request'] == '💎 Quant Discovery'
    assert app.session_state['qi_earnings_origin']


def test_response_size_and_successful_empty():
    for body, error in [(b'x' * 2_000_001, True), (b'{"earningsCalendar":[]}', False)]:
        with httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(200, content=body))) as client:
            result = CalendarService().load(CONFIG, START, END, client=client)
        assert bool(result.error) == error
        assert not result.events
        assert bool(result.retrieved_at) != error
