"""PostgreSQL ledger checks. No network/provider quota used in the test suite."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
import pytest

from app.intelligence.earnings_postgres_provider import PostgresEarningsAPIService

MONDAY = date(2026, 11, 9)
NOW = datetime(2026, 11, 9, 12, tzinfo=ZoneInfo("America/New_York")).timestamp()


def require_isolated_database(db, marker):
    """Read-only guard; a missing/empty ledger is not proof of isolation."""
    if not marker or not marker.startswith("qi-isolated-earnings-test:"):
        pytest.fail("An operator-provisioned isolated database marker is required", pytrace=False)
    actual = db.execute(
        "SELECT shobj_description(oid, 'pg_database') FROM pg_database "
        "WHERE datname=current_database()"
    ).fetchone()[0]
    if actual != marker:
        pytest.fail("Database isolation marker mismatch; no test writes allowed", pytrace=False)


def test_isolation_guard_rejects_unmarked_database():
    class Database:
        def execute(self, query):
            return self

        def fetchone(self):
            return (None,)

    for marker in (None, "", "production", "qi-isolated-earnings-test:disposable"):
        with pytest.raises(pytest.fail.Exception):
            require_isolated_database(Database(), marker)


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


def test_real_postgres_concurrent_reservation_if_test_database_provided():
    """Opt-in only: set EARNINGS_TEST_DATABASE_URL on an isolated test DB.

    The schema and matching database comment marker must be provisioned by an
    operator on the isolated branch. Never mark production to run this test.
    """
    import os
    from concurrent.futures import ThreadPoolExecutor
    from threading import Lock

    dsn = os.environ.get("EARNINGS_TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("An isolated PostgreSQL test database is required")
    import psycopg

    dsns = [dsn]
    if os.environ.get("EARNINGS_TEST_POOLED_DATABASE_URL"):
        dsns.append(os.environ["EARNINGS_TEST_POOLED_DATABASE_URL"])
    marker = os.environ.get("EARNINGS_TEST_DATABASE_MARKER")
    # Validate every endpoint before any writes, including the optional pooler.
    for endpoint in dsns:
        with psycopg.connect(endpoint) as db:
            require_isolated_database(db, marker)
            if db.execute("SELECT 1 FROM earnings_budget LIMIT 1").fetchone() or db.execute(
                "SELECT 1 FROM earnings_weeks LIMIT 1"
            ).fetchone():
                pytest.skip("Test ledgers have history; use a fresh isolated test branch/database")
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
        def load(index):
            return PostgresEarningsAPIService(dsns[index % len(dsns)]).load_week(
                "synthetic-key", MONDAY, now=NOW, client=http
            )
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(load, range(16)))
        assert sum(not result.error for result in results) >= 1
        assert len(calls) == 7
        assert not load(0).error
        assert len(calls) == 7
    # A new interpreter has no service/session memory. All HTTP is forbidden.
    import subprocess
    import sys

    reconnect = """
import os
import httpx
from app.intelligence.earnings_postgres_provider import PostgresEarningsAPIService
def forbidden(request):
    raise AssertionError('A reconnect must not fetch provider data')
with httpx.Client(transport=httpx.MockTransport(forbidden)) as http:
    result = PostgresEarningsAPIService(os.environ['EARNINGS_TEST_DATABASE_URL']).load_week(
        'synthetic-key', now=float(os.environ['EARNINGS_TEST_NOW']), client=http)
    if os.environ['EARNINGS_TEST_EXPECT_ERROR'] == '1':
        assert result.error and 'next automatic attempt' in result.error
    else:
        assert not result.error and len(result.events) == 7
"""
    # Credentials stay in inherited process memory/environment, never arguments
    # or files. Suppress driver traceback output, which may contain a DSN.
    def reconnect_without_http(now, expect_error=False):
        for endpoint in dsns:
            child = subprocess.run(
                [sys.executable, "-c", reconnect],
                env=dict(
                    os.environ, EARNINGS_TEST_DATABASE_URL=endpoint,
                    EARNINGS_TEST_NOW=str(now),
                    EARNINGS_TEST_EXPECT_ERROR=str(int(expect_error)),
                ),
                capture_output=True, timeout=30, check=False,
            )
            assert child.returncode == 0, "Fresh-process reuse failed (details suppressed)"

    reconnect_without_http(NOW)
    with psycopg.connect(dsn) as db:
        assert db.execute(
            "SELECT calls FROM earnings_budget WHERE month='2026-11'"
        ).fetchone()[0] == 7
        assert db.execute("SELECT count(*) FROM earnings_weeks").fetchone()[0] == 1
    # A failed batch still charges seven reservations and preserves its cooldown
    # across a process restart. This provider response is entirely synthetic.
    failed_requests = []

    def unavailable(request):
        failed_requests.append(request)
        return httpx.Response(503)

    later = NOW + 7 * 86400
    with httpx.Client(transport=httpx.MockTransport(unavailable)) as http:
        result = PostgresEarningsAPIService(dsn).load_week(
            "synthetic-key", MONDAY + timedelta(days=7), now=later, client=http,
        )
    assert result.error
    assert len(failed_requests) == 1
    reconnect_without_http(later, expect_error=True)
    with psycopg.connect(dsn) as db:
        assert db.execute(
            "SELECT calls FROM earnings_budget WHERE month='2026-11'"
        ).fetchone()[0] == 14
