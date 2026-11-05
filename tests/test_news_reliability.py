"""Deterministic tests for caching and provider resilience."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event

from app.intelligence.news_reliability import (
    NewsRateLimited,
    NewsReliability,
)


def setup_cache():
    current = [1000.0]
    cache = NewsReliability(
        fresh_seconds=10,
        stale_seconds=100,
        cooldown_seconds=30,
        clock=lambda: current[0],
    )
    return cache, current


def test_fresh_cache_avoids_duplicate_requests():
    cache, _ = setup_cache()
    calls = []

    def loader():
        calls.append(1)
        return [{"title": "Apple update"}]

    first = cache.fetch("gdelt", "AAPL:7:10", loader)
    second = cache.fetch("gdelt", "AAPL:7:10", loader)

    assert first.status == "live"
    assert second.status == "cached"
    assert len(calls) == 1


def test_cached_objects_cannot_be_modified_by_callers():
    cache, _ = setup_cache()
    first = cache.fetch(
        "gdelt", "AAPL", lambda: [{"title": "Original"}]
    )
    first.articles[0]["title"] = "Modified"

    second = cache.fetch("gdelt", "AAPL", lambda: [])
    assert second.articles[0]["title"] == "Original"


def test_stale_data_is_explicit_after_provider_failure():
    cache, now = setup_cache()
    cache.fetch("gdelt", "AAPL", lambda: [{"title": "Old"}])
    now[0] += 12

    def unavailable():
        raise ConnectionError("Provider offline")

    result = cache.fetch("gdelt", "AAPL", unavailable)

    assert result.status == "stale"
    assert result.age_seconds == 12
    assert result.articles[0]["title"] == "Old"


def test_rate_limit_prevents_followup_requests():
    cache, _ = setup_cache()
    calls = []

    def limited():
        calls.append(1)
        raise NewsRateLimited("429")

    first = cache.fetch("gdelt", "AAPL", limited)
    second = cache.fetch("gdelt", "NVDA", limited)

    assert first.status == "unavailable"
    assert second.status == "unavailable"
    assert len(calls) == 1


def test_provider_cooldown_is_independent():
    cache, _ = setup_cache()

    def limited():
        raise NewsRateLimited("429")

    cache.fetch("gdelt", "AAPL", limited)

    result = cache.fetch(
        "another_provider",
        "AAPL",
        lambda: [{"title": "Available"}],
    )

    assert result.status == "live"
    assert len(result.articles) == 1


def test_recovery_after_cooldown():
    cache, now = setup_cache()

    def limited():
        raise NewsRateLimited("429")

    cache.fetch("gdelt", "AAPL", limited)
    now[0] += 31

    result = cache.fetch(
        "gdelt", "AAPL",
        lambda: [{"title": "Recovered"}],
    )

    assert result.status == "live"


def test_expired_data_is_never_served():
    cache, now = setup_cache()
    cache.fetch("gdelt", "AAPL", lambda: [{"title": "Old"}])
    now[0] += 101

    def unavailable():
        raise ConnectionError("Offline")

    result = cache.fetch("gdelt", "AAPL", unavailable)

    assert result.status == "unavailable"
    assert result.articles == []


def test_invalid_provider_data_is_not_cached():
    cache, _ = setup_cache()

    result = cache.fetch("gdelt", "AAPL", lambda: {"invalid": True})

    assert result.status == "unavailable"


def test_cache_capacity_is_bounded():
    cache = NewsReliability(max_entries=2)

    for symbol in ("AAPL", "NVDA", "MSFT"):
        cache.fetch(
            "gdelt", symbol,
            lambda symbol=symbol: [{"title": symbol}],
        )

    assert len(cache._entries) == 2


def test_empty_news_results_are_cached():
    cache, _ = setup_cache()
    calls = []

    def loader():
        calls.append(1)
        return []

    first = cache.fetch("gdelt", "CELH", loader)
    second = cache.fetch("gdelt", "CELH", loader)

    assert first.status == "live"
    assert second.status == "cached"
    assert len(calls) == 1


def test_simultaneous_identical_requests_are_deduplicated():
    cache, _ = setup_cache()
    started = Event()
    release = Event()
    calls = []

    def loader():
        calls.append(1)
        started.set()
        assert release.wait(timeout=5)
        return [{"title": "One fetch"}]

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(cache.fetch, "gdelt", "AAPL", loader)
        assert started.wait(timeout=5)
        second = pool.submit(cache.fetch, "gdelt", "AAPL", loader)
        release.set()
        results = [first.result(timeout=5), second.result(timeout=5)]

    assert len(calls) == 1
    assert {result.status for result in results} == {"live", "cached"}
