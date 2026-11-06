"""Offline contract fixtures; these are not live events."""
from datetime import UTC, date

import httpx
import pytest
from streamlit.testing.v1 import AppTest

from app.intelligence.earnings_calendar import (
    CalendarConfig,
    CalendarService,
    normalize,
)

START, END = date(2026, 11, 2), date(2026, 11, 8)


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



@pytest.mark.parametrize("scope", ["", "personal_local", "written_agreement"])
def test_public_calendar_cannot_be_enabled(scope, monkeypatch):
    monkeypatch.setenv("FINNHUB_API_KEY", "test-secret")
    monkeypatch.setenv("QI_EARNINGS_USE", scope)
    def forbidden(request):
        pytest.fail("Public build attempted a provider request")
    service = CalendarService()
    service._cache["old-private-result"] = object()
    with httpx.Client(transport=httpx.MockTransport(forbidden)) as client:
        result = service.load(CalendarConfig("test-secret", scope), START, END, client=client)
    assert result.error and not result.events and result.retrieved_at is None
    assert not service._cache
    assert "test-secret" not in repr(CalendarConfig("test-secret", scope))


def test_public_earnings_page_is_educational(monkeypatch):
    import app.intelligence.earnings_calendar as calendar
    monkeypatch.setattr(calendar.calendar_service, "load", lambda *a, **k: pytest.fail("UI consulted provider"))
    app = AppTest.from_string("from dashboard.earnings_week import render_earnings_week\nrender_earnings_week()").run()
    assert not app.exception
    assert app.title[0].value == "Earnings calendar"
    assert not any("week" in b.label.lower() for b in app.button)
