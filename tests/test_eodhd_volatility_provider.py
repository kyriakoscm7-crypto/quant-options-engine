"""EODHD personal-use integration: no network calls without a durable reservation."""
from datetime import UTC, datetime, timedelta

import httpx
import numpy as np
import pytest

from app.intelligence.eodhd_volatility_provider import (
    DAILY_BUDGET,
    PostgresEODHDService,
    calculate_eodhd_hv,
    eodhd_symbol,
    normalize_eodhd,
)


def rows(length=90):
    start = datetime(2026, 6, 1, tzinfo=UTC)
    days = []
    current = start
    while len(days) < length:
        if current.weekday() < 5:
            days.append({
                "date": current.date().isoformat(),
                "adjusted_close": float(100 + len(days) * 0.2 + (-1) ** len(days)),
            })
        current += timedelta(days=1)
    return days


def test_ticker_mapping_us_only_and_exchanges():
    assert eodhd_symbol("NASDAQ:AMD") == "AMD.US"
    assert eodhd_symbol("NYSE:BRK.B") == "BRK-B.US"
    assert eodhd_symbol("AMEX:SPY") == "SPY.US"
    for invalid in ("AMD", "LSE:VOD", "NASDAQ:AMD?api_token=x", "NASDAQ:"):
        with pytest.raises(ValueError):
            eodhd_symbol(invalid)


def test_validated_adjusted_data_and_reproducible_volatility():
    frame = normalize_eodhd(rows())
    result = calculate_eodhd_hv(frame)
    assert len(result) == 90
    assert np.isfinite(result["HV20"].dropna()).all()
    assert np.isfinite(result["HV60"].dropna()).all()
    assert result["HV20"].iloc[:20].isna().all()
    assert result["HV60"].iloc[:60].isna().all()
    assert float(result["HV20"].iloc[-1]) > 0


def test_invalid_provider_response_fails_explicitly():
    samples = [
        {}, [], rows(20),
        rows() + [rows()[-1]],
        rows()[:-1] + [{"date": "2026-11-09", "adjusted_close": -1}],
    ]
    for payload in samples:
        with pytest.raises(ValueError):
            normalize_eodhd(payload)


def test_no_neon_connection_means_no_provider_requests(monkeypatch):
    import psycopg

    calls = []

    def forbidden_connection(*args, **kwargs):
        raise RuntimeError("Never disclose this simulated DSN!")

    monkeypatch.setattr(psycopg, "connect", forbidden_connection)

    def provider(request):
        calls.append(request)
        return httpx.Response(200, json=rows())

    with httpx.Client(transport=httpx.MockTransport(provider)) as http:
        result = PostgresEODHDService("postgresql://fake-secret@invalid/test").load(
            "AMD.US", api_key="not-real", now=datetime(2026, 11, 10, tzinfo=UTC),
            client=http,
        )
    assert result.error
    assert "fake-secret" not in str(result)
    assert calls == []


def test_missing_key_and_bad_ticker_never_issue_requests():
    service = PostgresEODHDService()
    assert service.load("AMD.US", api_key="").error
    assert service.load("../token", api_key="test").error
    assert service.load("AMD.US", api_key="test").error
    assert DAILY_BUDGET < 20
