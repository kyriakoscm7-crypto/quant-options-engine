"""Offline tests for live-company directory caching."""

from app.intelligence.company_directory_service import (
    CompanyDirectoryService,
)

RECORDS = {
    "0": {
        "ticker": "AAPL",
        "title": "Apple Inc.",
        "cik_str": 320193,
    },
    "1": {
        "ticker": "NVDA",
        "title": "NVIDIA Corporation",
        "cik_str": 1045810,
    },
}


def service_with_clock():
    now = [1000.0]
    calls = []

    def fetch():
        calls.append(1)
        return RECORDS

    service = CompanyDirectoryService(
        ttl_seconds=10,
        max_stale_seconds=100,
        fetcher=fetch,
        clock=lambda: now[0],
    )
    return service, now, calls


def test_initial_directory_download():
    service, _, _ = service_with_clock()
    snapshot = service.get()

    assert snapshot.status == "live"
    assert len(snapshot.registry.companies) == 2


def test_repeated_search_uses_cache():
    service, _, calls = service_with_clock()

    first, matches = service.search("AAPL")
    second, matches_again = service.search("Apple")

    assert first.status == "live"
    assert second.status == "cached"
    assert matches[0].ticker == "AAPL"
    assert matches_again[0].ticker == "AAPL"
    assert len(calls) == 1


def test_cache_refresh_after_ttl():
    service, now, calls = service_with_clock()

    service.get()
    now[0] += 11
    refreshed = service.get()

    assert refreshed.status == "live"
    assert len(calls) == 2


def test_stale_directory_is_labeled():
    now = [1000.0]
    calls = [0]

    def fetch():
        calls[0] += 1
        if calls[0] > 1:
            raise ConnectionError("SEC unavailable")
        return RECORDS

    service = CompanyDirectoryService(
        ttl_seconds=10,
        max_stale_seconds=100,
        fetcher=fetch,
        clock=lambda: now[0],
    )

    service.get()
    now[0] += 15
    snapshot = service.get()

    assert snapshot.status == "stale"
    assert snapshot.age_seconds == 15


def test_expired_directory_is_not_used():
    now = [1000.0]
    calls = [0]

    def fetch():
        calls[0] += 1
        if calls[0] > 1:
            raise ConnectionError("SEC unavailable")
        return RECORDS

    service = CompanyDirectoryService(
        ttl_seconds=10,
        max_stale_seconds=100,
        fetcher=fetch,
        clock=lambda: now[0],
    )

    service.get()
    now[0] += 101
    snapshot = service.get()

    assert snapshot.status == "unavailable"
    assert snapshot.registry is None


def test_empty_directory_is_rejected():
    service = CompanyDirectoryService(fetcher=lambda: {})

    assert service.get().status == "unavailable"


def test_initial_provider_failure():
    def unavailable():
        raise ConnectionError("Offline")

    service = CompanyDirectoryService(fetcher=unavailable)
    snapshot, matches = service.search("AAPL")

    assert snapshot.status == "unavailable"
    assert matches == []
