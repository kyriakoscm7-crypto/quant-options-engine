"""Bounded, source-linked news discovery using the original GDELT Project."""

import json
import re
from datetime import UTC, datetime, timedelta
from urllib.parse import urlsplit

import requests

from app.intelligence.news_reliability import NewsRateLimited, retry_after_seconds

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
MAX_BYTES = 2_000_000


def _valid_url(value: str) -> bool:
    try:
        parts = urlsplit(value)
        return (
            parts.scheme == "https"
            and bool(parts.hostname)
            and not parts.username
            and not parts.password
        )
    except ValueError:
        return False


def build_query(company_name: str) -> str:
    """Search a company name, not an ambiguous bare ticker."""
    name = company_name.strip()

    if not 3 <= len(name) <= 100:
        raise ValueError("Company name must have 3-100 characters.")

    if not re.fullmatch(r"[\w .,&'()/-]+", name, re.UNICODE):
        raise ValueError("Unsupported company-name characters.")

    # Prevent query-language operators from being supplied as a company name.
    if re.search(r"\b(?:AND|OR|NOT)\b", name, flags=re.IGNORECASE):
        raise ValueError("Search operators are not valid company names.")

    return '"' + name + '"'


def parse_articles(payload: dict, days: int, now=None) -> list[dict]:
    """Retain recent, linked articles without asserting issuer relevance."""
    if not isinstance(payload, dict):
        raise ValueError("Invalid GDELT response.")

    rows = payload.get("articles", [])
    if not isinstance(rows, list):
        raise ValueError("Invalid GDELT article collection.")

    now = now or datetime.now(UTC)
    earliest = now - timedelta(days=days)
    seen = set()
    results = []

    for row in rows:
        if not isinstance(row, dict):
            continue

        title = str(row.get("title") or "").strip()
        url = str(row.get("url") or "").strip()
        raw_date = str(row.get("seendate") or "").strip()

        if not title or not _valid_url(url):
            continue

        try:
            published = datetime.strptime(
                raw_date, "%Y%m%dT%H%M%SZ"
            ).replace(tzinfo=UTC)
        except ValueError:
            continue

        if published < earliest or published > now + timedelta(minutes=5):
            continue

        if url in seen:
            continue
        seen.add(url)

        results.append({
            "title": title[:500],
            "url": url,
            "publisher_domain": urlsplit(url).hostname,
            "published": published.isoformat(),
            "timestamp_kind": "first_seen",
            "language": str(row.get("language") or "")[:40],
            "source": "GDELT Project",
            "company_match": "unverified",
        })

    results.sort(key=lambda item: item["published"], reverse=True)
    return results


def fetch_gdelt_news(company_name: str, days: int = 7, limit: int = 30):
    """Fetch dated news metadata, with strict size and timeout limits."""
    if not isinstance(days, int) or not 1 <= days <= 30:
        raise ValueError("days must be 1-30.")
    if not isinstance(limit, int) or not 1 <= limit <= 75:
        raise ValueError("limit must be 1-75.")

    query = build_query(company_name)
    response = requests.get(
        GDELT_URL,
        params={
            "query": query,
            "mode": "ArtList",
            "format": "json",
            "sort": "DateDesc",
            "timespan": f"{days}d",
            "maxrecords": limit,
        },
        headers={
            "User-Agent": "QuantIntelligence/1.0 (news research)",
            "Accept": "application/json",
        },
        timeout=15,
        stream=True,
    )

    try:
        if response.status_code == 429:
            raise NewsRateLimited(
                "GDELT is temporarily rate-limiting news requests. "
                "Use cached results or another authorized provider.",
                retry_after_seconds(response),
            )

        response.raise_for_status()
        chunks = []
        size = 0

        for chunk in response.iter_content(chunk_size=65536):
            size += len(chunk)
            if size > MAX_BYTES:
                raise ValueError("GDELT response exceeds size limit.")
            chunks.append(chunk)

        payload = json.loads(b"".join(chunks))
    finally:
        response.close()

    return parse_articles(payload, days)[:limit]
