"""Regression tests for SEC event-date filing research."""

from datetime import date

import pytest

from app.intelligence.sec_filings import (
    fetch_sec_filings,
    filings_near_event,
    resolve_company,
    validate_user_agent,
)


def sample_submissions():
    return {
        "filings": {
            "recent": {
                "accessionNumber": [
                    "0001234567-26-000003",
                    "0001234567-26-000002",
                    "0001234567-26-000001",
                ],
                "filingDate": [
                    "2026-10-31",
                    "2026-10-30",
                    "2026-10-29",
                ],
                "form": ["8-K", "10-Q", "SC 13G"],
                "primaryDocument": [
                    "event.htm",
                    "quarterly.htm",
                    "ownership.htm",
                ],
                "primaryDocDescription": [
                    "Current report",
                    "Quarterly report",
                    "Ownership filing",
                ],
                "acceptanceDateTime": [
                    "2026-10-31T12:00:00Z",
                    "2026-10-30T11:00:00Z",
                    "2026-10-29T21:00:00Z",
                ],
            },
        },
    }


def test_resolve_exact_ticker():
    directory = {
        "0": {
            "ticker": "TEST",
            "cik_str": 1234567,
            "title": "Test Corporation",
        },
    }
    assert resolve_company("test", directory) == (
        1234567,
        "Test Corporation",
    )


def test_unknown_ticker_has_no_match():
    assert resolve_company("XYZ", {}) is None


def test_date_window_includes_nearby_filings():
    filings = filings_near_event(
        sample_submissions(),
        1234567,
        "2026-10-30",
    )
    assert len(filings) == 3


def test_same_day_timing_is_unverified():
    filings = filings_near_event(
        sample_submissions(),
        1234567,
        "2026-10-30",
    )
    same_day = next(
        item for item in filings
        if item["filing_date"] == "2026-10-30"
    )
    assert same_day["relationship"] == (
        "Same-day filing; timing unverified"
    )


def test_before_and_after_labels():
    filings = filings_near_event(
        sample_submissions(),
        1234567,
        date(2026, 10, 30),
    )
    relationships = {item["relationship"] for item in filings}

    assert "Filed before event date" in relationships
    assert "Filed after event date" in relationships


def test_distant_filings_excluded():
    assert filings_near_event(
        sample_submissions(),
        1234567,
        "2026-09-01",
    ) == []


def test_official_document_url():
    filings = filings_near_event(
        sample_submissions(),
        1234567,
        "2026-10-30",
    )
    assert filings[0]["url"] == (
        "https://www.sec.gov/Archives/edgar/data/1234567/"
        "000123456726000003/event.htm"
    )


def test_invalid_document_name_is_excluded():
    data = sample_submissions()
    data["filings"]["recent"]["primaryDocument"][0] = "../unsafe.htm"

    filings = filings_near_event(data, 1234567, "2026-10-30")

    assert len(filings) == 2


def test_too_small_window_excludes_prior_filing():
    filings = filings_near_event(
        sample_submissions(),
        1234567,
        "2026-10-30",
        before_days=0,
        after_days=0,
    )
    assert len(filings) == 1


def test_invalid_contact_header_is_rejected():
    with pytest.raises(ValueError):
        validate_user_agent("Mozilla/5.0")


def test_example_contact_is_rejected():
    with pytest.raises(ValueError):
        validate_user_agent("Research contact@example.com")


def test_negative_window_is_rejected():
    with pytest.raises(ValueError):
        filings_near_event(
            sample_submissions(),
            1234567,
            "2026-10-30",
            before_days=-1,
        )


def test_http_retrieval_uses_declared_contact(monkeypatch):
    calls = []
    directory = {
        "0": {
            "ticker": "TEST",
            "cik_str": 1234567,
            "title": "Test Corporation",
        },
    }

    class Response:
        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    responses = [Response(directory), Response(sample_submissions())]

    def fake_get(url, headers, timeout):
        calls.append((url, headers, timeout))
        return responses[len(calls) - 1]

    monkeypatch.setattr(
        "app.intelligence.sec_filings.requests.get",
        fake_get,
    )

    company, filings = fetch_sec_filings(
        "TEST",
        "2026-10-30",
        "Quant Research tester@research.test",
    )

    assert company == "Test Corporation"
    assert len(filings) == 3
    assert len(calls) == 2
    assert all(
        call[1]["User-Agent"] == "Quant Research tester@research.test"
        for call in calls
    )
