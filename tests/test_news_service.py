"""Offline integration tests for the cached news service."""

import pytest

from app.intelligence.news_reliability import (
    NewsRateLimited,
    NewsReliability,
)
from app.intelligence.news_service import get_company_news


def new_cache():
    now = [1000.0]
    cache = NewsReliability(
        fresh_seconds=10,
        stale_seconds=100,
        cooldown_seconds=30,
        clock=lambda: now[0],
    )
    return cache, now


def test_repeated_search_only_calls_provider_once():
    cache, _ = new_cache()
    calls = []

    def loader(name, days, limit):
        calls.append((name, days, limit))
        return [{"title": "New filing"}]

    first = get_company_news("Apple Inc.", cache=cache, loader=loader)
    second = get_company_news("Apple Inc.", cache=cache, loader=loader)

    assert first.status == "live"
    assert second.status == "cached"
    assert len(calls) == 1


def test_company_names_are_separate_cache_keys():
    cache, _ = new_cache()
    calls = []

    def loader(name, days, limit):
        calls.append(name)
        return [{"title": name}]

    get_company_news("Apple Inc.", cache=cache, loader=loader)
    get_company_news("NVIDIA Corporation", cache=cache, loader=loader)

    assert calls == ["Apple Inc.", "NVIDIA Corporation"]


def test_date_windows_are_independent():
    cache, _ = new_cache()
    calls = []

    def loader(name, days, limit):
        calls.append(days)
        return []

    get_company_news("Apple Inc.", days=3, cache=cache, loader=loader)
    get_company_news("Apple Inc.", days=7, cache=cache, loader=loader)

    assert calls == [3, 7]


def test_result_limits_are_independent():
    cache, _ = new_cache()
    calls = []

    def loader(name, days, limit):
        calls.append(limit)
        return []

    get_company_news("Apple Inc.", limit=10, cache=cache, loader=loader)
    get_company_news("Apple Inc.", limit=30, cache=cache, loader=loader)

    assert calls == [10, 30]


def test_rate_limit_returns_explicit_unavailable_status():
    cache, _ = new_cache()

    def limited(name, days, limit):
        raise NewsRateLimited("429")

    result = get_company_news(
        "Apple Inc.", cache=cache, loader=limited
    )

    assert result.status == "unavailable"
    assert result.articles == []


def test_stale_fallback_is_labeled():
    cache, now = new_cache()

    get_company_news(
        "Apple Inc.",
        cache=cache,
        loader=lambda *args, **kwargs: [{"title": "Older"}],
    )

    now[0] += 15

    def unavailable(name, days, limit):
        raise ConnectionError("Offline")

    result = get_company_news(
        "Apple Inc.", cache=cache, loader=unavailable
    )

    assert result.status == "stale"
    assert result.age_seconds == 15


def test_no_articles_is_not_provider_failure():
    cache, _ = new_cache()

    result = get_company_news(
        "Celsius Holdings",
        cache=cache,
        loader=lambda *args, **kwargs: [],
    )

    assert result.status == "live"
    assert result.articles == []


@pytest.mark.parametrize(
    "name,days,limit",
    [
        ("", 7, 10),
        ("Apple Inc.", 0, 10),
        ("Apple Inc.", 31, 10),
        ("Apple Inc.", 7, 0),
        ("Apple Inc.", 7, 76),
        ("Apple Inc.", True, 10),
        ("Apple Inc.", 7, True),
        ("AAPL OR x", 7, 10),
    ],
)
def test_invalid_inputs_rejected(name, days, limit):
    cache, _ = new_cache()

    with pytest.raises(ValueError):
        get_company_news(
            name,
            days=days,
            limit=limit,
            cache=cache,
            loader=lambda *args, **kwargs: [],
        )
