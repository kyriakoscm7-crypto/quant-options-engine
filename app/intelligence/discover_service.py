"""Compose identity, SEC evidence and separately admitted licensed providers."""
from datetime import UTC, datetime

from app.intelligence.company_registry import CompanyRegistry
from app.intelligence.discover_evidence import corroborate
from app.intelligence.discover_financials import financial_health, normalized_filings


def company_deep_dive(gateway, ticker, *, providers=(), now=None):
    now = now or datetime.now(UTC)
    directory = gateway.fetch("directory")
    company = CompanyRegistry(directory["data"]).resolve_ticker(ticker)
    if company is None:
        raise LookupError("No verified SEC identity for this ticker")
    submissions = gateway.fetch("submissions", company.cik)
    if str(submissions["data"].get("cik", "")).lstrip("0") != company.cik.lstrip("0"):
        raise ValueError("Submissions identity mismatch")
    facts = None
    failures = []
    try:
        facts = gateway.fetch("companyfacts", company.cik)
        health = financial_health(facts["data"], company.cik, today=now.date())
    except (ValueError, RuntimeError, OSError):
        health = None
        failures.append("Financial health unavailable; no replacement values used")
    evidence = []
    for provider in providers:
        try:
            evidence.extend(provider.evidence(company.cik))
        except (ValueError, RuntimeError, OSError):
            failures.append("An optional evidence provider is unavailable")
    return {"company": company, "health": health,
            "filings": normalized_filings(submissions["data"], company.cik, now.date()),
            "sources": [directory, submissions] + ([facts] if facts else []),
            "earnings": corroborate(evidence, company.cik, "earnings", now=now),
            "analysts": corroborate(evidence, company.cik, "analyst_sentiment", now=now),
            "issues": failures}
