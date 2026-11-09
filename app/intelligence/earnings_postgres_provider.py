"""Durable, cross-instance EarningsAPI snapshot and quota ledger for PostgreSQL.

Schema must be provisioned before enabling the feature. Every failed storage
operation fails closed; the API is NEVER called without a committed reservation.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict
from datetime import UTC, date, datetime, timedelta

import httpx

from app.intelligence.earnings_api_provider import (
    API_URL,
    ET,
    MONTHLY_REQUEST_BUDGET,
    RETRY_SECONDS,
    WEEK_REQUESTS,
    EarningsEvent,
    WeekResult,
    cache_expiry,
    normalize_day,
    reporting_week,
)


class PostgresEarningsAPIService:
    """Coordinate all application replicas using one PostgreSQL database.

    The monthly row is locked before reading the weekly snapshot. This provides
    serialization for concurrent first visitors even across independent hosts.
    Requests are charged *and committed* before any external HTTP request.
    """

    def __init__(self, database_url=None):
        self.database_url = database_url

    def load_week(self, api_key, monday=None, *, client=None, now=None, database_url=None):
        now = time.time() if now is None else now
        selected = reporting_week(datetime.fromtimestamp(now, UTC))
        if monday is not None and monday != selected:
            return WeekResult(error="Only the automatic reporting week is available.")
        if not isinstance(api_key, str) or not api_key.strip():
            return WeekResult(error="Configure EARNINGSAPI_API_KEY on the server.")
        dsn = self.database_url or database_url
        if not dsn:
            return WeekResult(error="Persistent earnings database is not configured; showing issuer announcements.")
        try:
            return self._load(dsn, api_key, selected, client, now)
        except Exception:
            # Database driver errors, missing schema, malformed cache, or failure
            # to store fetched data must not trigger requests from an untracked host.
            # Do not include exceptions: driver errors can contain credentials.
            return WeekResult(error="Earnings database unavailable; no untracked requests will be made.")

    def _load(self, dsn, api_key, monday, client, now):
        import psycopg

        week = monday.isoformat()
        month = datetime.fromtimestamp(now, ET).strftime("%Y-%m")
        with psycopg.connect(dsn, connect_timeout=4) as db:  # noqa: SIM117
            with db.transaction():
                # Serialize all leases in a given calendar month. The later
                # SELECT runs after a competing transaction commits.
                db.execute(
                    "INSERT INTO earnings_budget (month, calls) VALUES (%s, 0) "
                    "ON CONFLICT (month) DO NOTHING", (month,)
                )
                used = db.execute(
                    "SELECT calls FROM earnings_budget WHERE month=%s FOR UPDATE",
                    (month,)
                ).fetchone()[0]
                row = db.execute(
                    "SELECT next_attempt, payload, fetched FROM earnings_weeks WHERE week=%s",
                    (week,)
                ).fetchone()
                if row and row[1] is not None and row[2] is not None and now < cache_expiry(row[2], monday):
                    saved = json.loads(row[1])
                    events = tuple(
                        EarningsEvent(**dict(e, day=date.fromisoformat(e["day"])))
                        for e in saved["events"]
                    )
                    return WeekResult(
                        events=events, retrieved_at=row[2], rejected=saved["rejected"],
                        cache_expires_at=cache_expiry(row[2], monday),
                    )
                if row and now < row[0]:
                    return WeekResult(
                        error="Calendar refresh pending or unavailable; next automatic attempt after "
                        + datetime.fromtimestamp(row[0], ET).strftime("%b %d, %Y %I:%M %p ET") + "."
                    )
                if used + WEEK_REQUESTS > MONTHLY_REQUEST_BUDGET:
                    return WeekResult(error="Calendar monthly request budget reached; showing issuer announcements.")
                # Reserve all seven requests AND cooldown in the same durable
                # transaction. A crash, 429, or process restart cannot refund it.
                db.execute(
                    "UPDATE earnings_budget SET calls=calls+%s WHERE month=%s",
                    (WEEK_REQUESTS, month),
                )
                db.execute(
                    "INSERT INTO earnings_weeks (week, next_attempt, payload, fetched) "
                    "VALUES (%s, %s, NULL, NULL) "
                    "ON CONFLICT (week) DO UPDATE SET next_attempt=EXCLUDED.next_attempt, "
                    "payload=NULL, fetched=NULL",
                    (week, now + RETRY_SECONDS),
                )
                db.execute(
                    "UPDATE earnings_weeks SET payload=NULL, fetched=NULL "
                    "WHERE week <> %s AND payload IS NOT NULL",
                    (week,),
                )
            # The context transaction has committed before the HTTP phase.
        try:
            if client is None:
                with httpx.Client() as http:
                    result = self._fetch(http, api_key, monday, now)
            else:
                result = self._fetch(client, api_key, monday, now)
        except (httpx.HTTPError, ValueError, TypeError):
            return WeekResult(
                error="EarningsAPI unavailable. Automatic retry is paused for 24 hours; showing issuer announcements."
            )

        payload = json.dumps({
            "events": [dict(asdict(e), day=e.day.isoformat()) for e in result.events],
            "rejected": result.rejected,
        })
        with psycopg.connect(dsn, connect_timeout=4) as db:  # noqa: SIM117
            with db.transaction():
                updated = db.execute(
                    "UPDATE earnings_weeks SET payload=%s, fetched=%s "
                    "WHERE week=%s AND next_attempt=%s",
                    (payload, now, week, now + RETRY_SECONDS),
                )
                # Do not claim a durable cache if the reservation was changed
                # or removed by a competing process.
                if updated.rowcount != 1:
                    raise ValueError("Reservation changed")
        return result

    @staticmethod
    def _fetch(http, api_key, monday, now):
        events, rejected = [], 0
        for offset in range(WEEK_REQUESTS):
            day = monday + timedelta(days=offset)
            response = http.get(
                API_URL, params={"date": day.isoformat(), "apikey": api_key},
                timeout=12.0, follow_redirects=False,
            )
            if response.status_code != 200:
                raise ValueError("Provider unavailable")
            found, invalid = normalize_day(response.json(), day)
            events.extend(found)
            rejected += invalid
        return WeekResult(
            events=tuple(sorted(events, key=lambda e: (e.day, e.session, e.symbol))),
            retrieved_at=now, rejected=rejected, cache_expires_at=cache_expiry(now, monday),
        )


postgres_earnings_service = PostgresEarningsAPIService()
