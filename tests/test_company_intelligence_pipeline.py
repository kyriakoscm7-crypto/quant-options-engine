"""Offline integration tests for company-specific news intelligence."""

import pytest

from app.intelligence.company_intelligence_pipeline import (
    build_company_report,
)
from app.intelligence.company_registry import CompanyRegistry
from app.intelligence.news_reliability import (
    NewsRateLimited,
    NewsReliability,
)


@pytest.fixture
def registry():
    return CompanyRegistry({
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
    })


@pytest.fixture
def cache():
    return NewsReliability(
        fresh_seconds=10,
        stale_seconds=100,
        cooldown_seconds=30,
    )


def test_exact_company_article_is_likely(registry, cache):
    report = build_company_report(
        registry,
        "AAPL",
        cache=cache,
        loader=lambda *a, **k: [
            {"title": "Apple Inc. announces quarterly results"}
        ],
    )

    assert report.company.cik == "0000320193"
    assert len(report.likely_articles) == 1
    assert report.provider_status == "live"


def test_unrelated_article_is_excluded(registry, cache):
    report = build_company_report(
        registry,
        "AAPL",
        cache=cache,
        aliases=("Apple",),
        loader=lambda *a, **k: [
            {"title": "Apple farmers celebrate record harvest"}
        ],
    )

    assert len(report.likely_articles) == 0
    assert report.unmatched_count == 1


def test_uncertain_match_goes_to_review(registry, cache):
    report = build_company_report(
        registry,
        "AAPL",
        cache=cache,
        aliases=("Apple",),
        loader=lambda *a, **k: [
            {"title": "Apple shares rise before earnings"}
        ],
    )

    assert len(report.review_articles) == 1
    assert len(report.likely_articles) == 0


def test_distinctive_context_supports_match(registry, cache):
    report = build_company_report(
        registry,
        "AAPL",
        cache=cache,
        aliases=("Apple",),
        distinctive_terms=("MacBook",),
        loader=lambda *a, **k: [
            {"title": "Apple introduces new MacBook models"}
        ],
    )

    assert len(report.likely_articles) == 1


def test_no_unreviewed_alias_is_invented(registry, cache):
    report = build_company_report(
        registry,
        "NVDA",
        cache=cache,
        loader=lambda *a, **k: [
            {"title": "NVIDIA unveils new AI hardware"}
        ],
    )

    assert len(report.likely_articles) == 0
    assert report.unmatched_count == 1


def test_same_company_search_reuses_cached_news(registry, cache):
    calls = []

    def loader(*args, **kwargs):
        calls.append(1)
        return [{"title": "Apple Inc. reports earnings"}]

    build_company_report(
        registry, "AAPL", cache=cache, loader=loader
    )
    report = build_company_report(
        registry, "AAPL", cache=cache, loader=loader
    )

    assert len(calls) == 1
    assert report.provider_status == "cached"


def test_rate_limit_does_not_look_like_no_news(registry, cache):
    def limited(*args, **kwargs):
        raise NewsRateLimited("429")

    report = build_company_report(
        registry, "AAPL", cache=cache, loader=limited
    )

    assert report.provider_status == "unavailable"
    assert "No coverage conclusion" in report.coverage_warning


def test_empty_provider_result_is_distinguished(registry, cache):
    report = build_company_report(
        registry,
        "AAPL",
        cache=cache,
        loader=lambda *a, **k: [],
    )

    assert report.provider_status == "live"
    assert report.total_candidates == 0
    assert "No articles returned" in report.coverage_warning


def test_unknown_company_is_rejected(registry, cache):
    with pytest.raises(LookupError):
        build_company_report(
            registry,
            "UNKNOWN",
            cache=cache,
            loader=lambda *a, **k: [],
        )


def test_unverified_exchange_is_not_assumed(registry, cache):
    with pytest.raises(ValueError, match="unqualified"):
        build_company_report(
            registry,
            "NASDAQ:AAPL",
            cache=cache,
            loader=lambda *a, **k: [],
        )


def test_company_results_remain_separate(registry, cache):
    calls = []

    def loader(name, days, limit):
        calls.append(name)
        return [{"title": f"{name} announces results"}]

    apple = build_company_report(
        registry, "AAPL", cache=cache, loader=loader
    )
    nvidia = build_company_report(
        registry, "NVDA", cache=cache, loader=loader
    )

    assert len(calls) == 2
    assert apple.company.cik != nvidia.company.cik
    assert len(apple.likely_articles) == 1
    assert len(nvidia.likely_articles) == 1


def test_invalid_reviewed_metadata_rejected(registry, cache):
    with pytest.raises(ValueError, match="metadata"):
        build_company_report(
            registry,
            "AAPL",
            aliases=("Apple", 123),
            cache=cache,
            loader=lambda *a, **k: [],
        )
