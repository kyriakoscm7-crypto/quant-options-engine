"""PostgreSQL ledger checks. No network/provider quota used in the test suite."""
from datetime import date, datetime
from zoneinfo import ZoneInfo

import httpx
import pytest

from app.intelligence.earnings_postgres_provider import PostgresEarningsAPIService

MONDAY = date(2026, 11, 9)
NOW = datetime(2026, 11, 9, 12, tzinfo=ZoneInfo("America/New_York")).timestamp()


def test_postgres_without_connection_fails_closed():
    service = PostgresEarningsAPIService()
    assert service.load_week("api-key", MONDAY, now=NOW).error
    assert service.load_week("", MONDAY, now=NOW).error


def test_postgres_connect_failure_never_spends_api_quota(monkeypatch):
    import psycopg

    calls = []
    def denied(*args, **kwargs):
        raise RuntimeError("simulated database outage with secret credentials")
    monkeypatch.setattr(psycopg, "connect", denied)

    def provider(request):
        calls.append(request)
        return httpx.Response(200, json={})

    with httpx.Client(transport=httpx.MockTransport(provider)) as client:
        result = PostgresEarningsAPIService("postgresql://invalid-secret@localhost/fake").load_week(
            "fake-api-key", MONDAY, now=NOW, client=client
        )
    assert "database unavailable" in result.error.lower()
    assert "invalid-secret" not in repr(result)
    assert calls == []


def test_wrong_week_is_rejected_before_database_contact(monkeypatch):
    import psycopg

    def no_connection(*args, **kwargs):
        pytest.fail("unexpected PostgreSQL connection")
    monkeypatch.setattr(psycopg, "connect", no_connection)
    result = PostgresEarningsAPIService("postgresql://test").load_week(
        "key", MONDAY.replace(day=16), now=NOW
    )
    assert "automatic reporting week" in result.error


@pytest.mark.integration
def test_real_postgres_concurrent_reservation_if_test_database_provided():
    """Opt-in only: set EARNINGS_TEST_DATABASE_URL on an isolated test DB.

    The schema must be applied before running. Do NOT point this at production.
    """
    import os
    from concurrent.futures import ThreadPoolExecutor
    from threading import Lock

    dsn = os.environ.get("EARNINGS_TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("An isolated PostgreSQL test database is required")
    import psycopg

    with psycopg.connect(dsn) as db:
        db.execute("DELETE FROM earnings_weeks")
        db.execute("DELETE FROM earnings_budget")
        db.commit()
    calls = []
    guard = Lock()

    def response(request):
        with guard:
            calls.append(request)
        return httpx.Response(200, json={
            "date": request.url.params["date"],
            "pre": [{"symbol": "TEST", "name": "Synthetic Test"}],
            "after": [], "notSupplied": [],
        })

    with httpx.Client(transport=httpx.MockTransport(response)) as http:
        def load(_):
            return PostgresEarningsAPIService(dsn).load_week(
                "synthetic-key", MONDAY, now=NOW, client=http
            )
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(load, range(16)))
        assert sum(not result.error for result in results) >= 1
        assert len(calls) == 7
        assert not load(0).error
    with psycopg.connect(dsn) as db:
        assert db.execute(
            "SELECT calls FROM earnings_budget WHERE month='2026-11'"
        ).fetchone()[0] == 7
