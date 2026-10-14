"""News retrieval for Quant Intelligence."""

import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

import requests


def fetch_company_news(
    ticker: str,
    company_name: str = "",
    days: int = 7,
    limit: int = 12,
) -> list[dict]:
    """Retrieve recent company news from Google News RSS."""

    ticker = ticker.strip().upper()

    if not ticker:
        raise ValueError("A ticker symbol is required.")

    if not 1 <= days <= 30:
        raise ValueError("days must be between 1 and 30.")

    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100.")

    query_name = company_name.strip() or ticker

    response = requests.get(
        "https://news.google.com/rss/search",
        params={
            "q": f'"{query_name}" stock when:{days}d',
            "hl": "en-US",
            "gl": "US",
            "ceid": "US:en",
        },
        headers={
            "User-Agent": "Mozilla/5.0 QuantIntelligence/1.0",
        },
        timeout=15,
    )

    response.raise_for_status()

    root = ET.fromstring(response.content)

    results = []
    seen = set()
    now = datetime.now(UTC)

    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        publisher = (item.findtext("source") or "Unknown").strip()
        link = (item.findtext("link") or "").strip()
        published_raw = item.findtext("pubDate") or ""

        if not title or not link:
            continue

        try:
            published = parsedate_to_datetime(published_raw)
            if published.tzinfo is None:
                published = published.replace(tzinfo=UTC)
            published = published.astimezone(UTC)
        except (TypeError, ValueError):
            continue

        age_seconds = (now - published).total_seconds()

        if age_seconds < -3600 or age_seconds > days * 86400:
            continue

        normalized_title = title.casefold()

        if normalized_title in seen:
            continue

        seen.add(normalized_title)

        results.append({
            "title": title,
            "publisher": publisher,
            "published": published.isoformat(),
            "url": link,
        })

    results.sort(
        key=lambda article: article["published"],
        reverse=True,
    )

    return results[:limit]
