"""Unified source-linked research with explicit rights and coverage diagnostics."""

import json
import os
from dataclasses import dataclass
from datetime import UTC, date, datetime
from urllib.parse import urlsplit, urlunsplit

import requests

from app.intelligence.company_news_relevance import classify_headline
from app.intelligence.gdelt_news import fetch_gdelt_news
from app.intelligence.news_engine import fetch_company_news
from app.intelligence.news_reliability import (
    NewsRateLimited,
    NewsReliability,
    retry_after_seconds,
)
from app.intelligence.sec_company_directory import _declared_user_agent
from app.intelligence.sec_filings import filings_near_event


@dataclass(frozen=True)
class Provider:
    name: str
    loader: object
    enabled: bool = False
    rights_reference: str = ""


@dataclass(frozen=True)
class IntelligenceReport:
    company: object
    articles: tuple
    filings: tuple
    diagnostics: tuple
    rejected: int
    duplicates: int
    as_of: str


def configured_providers():
    """Fail closed: operator must record rights evidence for headline display."""
    return (
        Provider("Google News RSS", _google_loader,
                 os.getenv("QI_GOOGLE_NEWS_ENABLED") == "true",
                 os.getenv("QI_GOOGLE_NEWS_RIGHTS_REFERENCE", "")),
        Provider("GDELT", fetch_gdelt_news,
                 os.getenv("QI_GDELT_ENABLED") == "true",
                 os.getenv("QI_GDELT_RIGHTS_REFERENCE", "")),
    )


def _google_loader(name, **kwargs):
    return fetch_company_news("COMPANY", name, **kwargs)


def fetch_submissions(company):
    """Use the resolved CIK directly; never re-download the ticker directory."""
    response = requests.get(
        f"https://data.sec.gov/submissions/CIK{company.cik}.json",
        headers={"User-Agent": _declared_user_agent(), "Accept": "application/json"},
        timeout=15, stream=True,
    )
    try:
        if response.status_code == 429:
            raise NewsRateLimited("SEC rate limit", retry_after_seconds(response))
        response.raise_for_status()
        chunks, size = [], 0
        for chunk in response.iter_content(65536):
            size += len(chunk)
            if size > 10_000_000:
                raise ValueError("SEC submissions exceed size limit")
            chunks.append(chunk)
        payload = json.loads(b"".join(chunks))
        if str(payload.get("cik", "")).lstrip("0") != company.cik.lstrip("0"):
            raise ValueError("SEC submissions identity mismatch")
        if not isinstance(payload.get("filings", {}).get("recent"), dict):
            raise ValueError("Invalid SEC submissions")
        return payload
    finally:
        response.close()


class NewsEventsService:
    """Process-local caches; source failures remain separate from empty coverage."""

    def __init__(self, providers=(), filings_loader=fetch_submissions, cache=None):
        if len({p.name for p in providers}) != len(providers):
            raise ValueError("Provider names must be unique")
        self.providers = tuple(providers)
        self.filings_loader = filings_loader
        self.cache = cache or NewsReliability()

    def build(self, company, *, days=7, event_date=None, now=None):
        if isinstance(days, bool) or not isinstance(days, int) or not 1 <= days <= 30:
            raise ValueError("Window must be 1-30 days")
        now = now or datetime.now(UTC)
        if now.tzinfo is None:
            raise ValueError("A timezone-aware clock is required")
        day = date.fromisoformat(str(event_date or now.date()))
        articles, diagnostics, seen_urls, seen_titles = [], [], set(), set()
        rejected = duplicates = 0
        for provider in self.providers:
            if not provider.enabled or not provider.rights_reference.strip():
                diagnostics.append({"source": provider.name, "status": "disabled",
                                    "age_seconds": None, "message": "Requires enablement and recorded headline-display rights."})
                continue
            key = f"{company.cik}|{company.name}|{days}|75|{provider.rights_reference}"
            result = self.cache.fetch(provider.name, key,
                                      lambda p=provider: p.loader(company.name, days=days, limit=75))
            diagnostics.append({"source": provider.name, "status": result.status,
                                "age_seconds": result.age_seconds, "message": result.message})
            for row in result.articles:
                try:
                    title = row["title"].strip()
                    url = urlsplit(row["url"])
                    published = datetime.fromisoformat(row["published"].replace("Z", "+00:00"))
                    age = (now - published).total_seconds()
                    if (not title or len(title) > 1000 or url.scheme not in ("http", "https")
                            or not url.hostname or url.username or url.password
                            or age < 0 or age > days * 86400):
                        raise ValueError("Invalid metadata")
                    canonical = urlunsplit((url.scheme.lower(), url.netloc.lower(), url.path, url.query, ""))
                except (KeyError, TypeError, ValueError, AttributeError):
                    rejected += 1
                    continue
                title_key = " ".join(title.casefold().split())
                if canonical in seen_urls or title_key in seen_titles:
                    duplicates += 1
                    continue
                seen_urls.add(canonical)
                seen_titles.add(title_key)
                relevance = classify_headline(title, company.name)
                articles.append({"title": title, "url": canonical, "published": published.astimezone(UTC).isoformat(),
                                 "publisher": str(row.get("publisher") or row.get("publisher_domain") or url.hostname),
                                 "timestamp_kind": row.get("timestamp_kind", "published"),
                                 "source": provider.name, "relevance": relevance.status, "reason": relevance.reason})
        # Cache raw recent submissions independently of the chosen event window.
        sec = self.cache.fetch("SEC", company.cik, lambda: [self.filings_loader(company)])
        diagnostics.append({"source": "SEC", "status": sec.status,
                            "age_seconds": sec.age_seconds, "message": sec.message})
        filings = filings_near_event(sec.articles[0], int(company.cik), day,
                                    before_days=days, after_days=0, limit=100) if sec.articles else []
        articles.sort(key=lambda a: a["published"], reverse=True)
        return IntelligenceReport(company, tuple(articles), tuple(filings), tuple(diagnostics),
                                  rejected, duplicates, now.isoformat())
