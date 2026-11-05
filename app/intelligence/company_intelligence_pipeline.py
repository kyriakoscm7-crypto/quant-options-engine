"""Combine company identity, cached news and relevance evidence."""

from dataclasses import dataclass

from app.intelligence.company_news_relevance import classify_headline
from app.intelligence.company_registry import CompanyRegistry
from app.intelligence.news_service import get_company_news


@dataclass(frozen=True)
class ClassifiedArticle:
    article: dict
    relevance: str
    reason: str
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class CompanyIntelligenceReport:
    company: object
    provider_status: str
    provider_age_seconds: int | None
    provider_message: str
    likely_articles: tuple[ClassifiedArticle, ...]
    review_articles: tuple[ClassifiedArticle, ...]
    unmatched_count: int
    total_candidates: int

    @property
    def coverage_warning(self) -> str:
        if self.provider_status == "unavailable":
            return "News unavailable. No coverage conclusion can be drawn."
        if self.provider_status == "stale":
            return "Showing older cached results; freshness is not guaranteed."
        if self.total_candidates == 0:
            return "No articles returned by this provider and query."
        if not self.likely_articles:
            return "No strong company matches in the returned candidates."
        return (
            "Headline matches are heuristic, not independent "
            "verification of the reported events."
        )


def build_company_report(
    registry: CompanyRegistry,
    ticker: str,
    *,
    days: int = 7,
    limit: int = 30,
    aliases: tuple[str, ...] = (),
    distinctive_terms: tuple[str, ...] = (),
    cache=None,
    loader=None,
) -> CompanyIntelligenceReport:
    """Resolve a company before fetching and classifying its news.

    This service is intentionally limited to SEC registry identities.
    It does not automatically validate exchanges or international listings.
    """
    if not isinstance(registry, CompanyRegistry):
        raise ValueError("A validated CompanyRegistry is required.")

    if not isinstance(aliases, tuple) or not isinstance(
        distinctive_terms, tuple
    ):
        raise ValueError("Reviewed metadata must be provided as tuples.")

    if not all(
        isinstance(value, str)
        for value in aliases + distinctive_terms
    ):
        raise ValueError("Reviewed metadata must contain text only.")

    company = registry.resolve_ticker(ticker)

    if company is None:
        raise LookupError(
            "Company not found in the available SEC ticker directory."
        )

    result = get_company_news(
        company.name,
        days=days,
        limit=limit,
        cache=cache,
        loader=loader,
    )

    likely = []
    review = []
    unmatched = 0

    for article in result.articles:
        title = article.get("title")

        if not isinstance(title, str):
            unmatched += 1
            continue

        relevance = classify_headline(
            title,
            company.name,
            aliases=aliases,
            distinctive_terms=distinctive_terms,
        )

        classified = ClassifiedArticle(
            article=dict(article),
            relevance=relevance.status,
            reason=relevance.reason,
            evidence=relevance.evidence,
        )

        if relevance.status == "likely":
            likely.append(classified)
        elif relevance.status == "needs_review":
            review.append(classified)
        else:
            unmatched += 1

    return CompanyIntelligenceReport(
        company=company,
        provider_status=result.status,
        provider_age_seconds=result.age_seconds,
        provider_message=result.message,
        likely_articles=tuple(likely),
        review_articles=tuple(review),
        unmatched_count=unmatched,
        total_candidates=len(result.articles),
    )
