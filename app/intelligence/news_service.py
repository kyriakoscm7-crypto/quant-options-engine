"""Cached company-news access with explicit availability states."""

from app.intelligence.gdelt_news import fetch_gdelt_news
from app.intelligence.news_reliability import (
    NewsReliability,
    NewsResult,
)

_NEWS_CACHE = NewsReliability(
    fresh_seconds=900,
    stale_seconds=86400,
    cooldown_seconds=300,
    max_entries=2048,
)


def get_company_news(
    company_name: str,
    days: int = 7,
    limit: int = 30,
    *,
    cache: NewsReliability | None = None,
    loader=None,
) -> NewsResult:
    """Return cached news with honest freshness/availability labels."""
    name = company_name.strip()

    if not 3 <= len(name) <= 100:
        raise ValueError("Invalid company name.")

    if not isinstance(days, int) or isinstance(days, bool):
        raise ValueError("Invalid date window.")

    if not 1 <= days <= 30:
        raise ValueError("Date window must be 1-30 days.")

    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValueError("Invalid result limit.")

    if not 1 <= limit <= 75:
        raise ValueError("Result limit must be 1-75.")

    # Reuse the GDELT query validator before cache lookup.
    from app.intelligence.gdelt_news import build_query

    build_query(name)

    if loader is None:
        return NewsResult([], "unavailable", None, "External headline feeds are disabled in the public build.")

    active_cache = cache if cache is not None else _NEWS_CACHE
    active_loader = loader if loader is not None else fetch_gdelt_news

    key = f"{name.casefold()}|{days}|{limit}"

    return active_cache.fetch(
        "gdelt",
        key,
        lambda: active_loader(name, days=days, limit=limit),
    )
