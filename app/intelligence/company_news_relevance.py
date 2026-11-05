"""Conservative headline matching against known company identities."""

import re
import unicodedata
from dataclasses import dataclass

MARKET_TERMS = (
    "stock", "stocks", "share", "shares", "earnings",
    "revenue", "investors", "guidance", "nasdaq",
    "nyse", "quarterly results", "market cap",
)


@dataclass(frozen=True)
class RelevanceResult:
    status: str
    reason: str
    evidence: tuple[str, ...] = ()


def _normalize(text: str) -> str:
    """Normalize Unicode and whitespace while retaining word boundaries."""
    text = unicodedata.normalize("NFKC", text).casefold()
    return re.sub(r"\s+", " ", text).strip()


def _contains(text: str, phrase: str) -> bool:
    """Match complete words or phrases, not substrings."""
    phrase = _normalize(phrase)
    if not phrase:
        return False

    return bool(
        re.search(
            r"(?<!\w)" + re.escape(phrase) + r"(?!\w)",
            text,
        )
    )


def classify_headline(
    title: str,
    company_name: str,
    *,
    aliases: tuple[str, ...] = (),
    distinctive_terms: tuple[str, ...] = (),
) -> RelevanceResult:
    """Classify headline identity evidence, not factual truth.

    Aliases and distinctive terms must come from reviewed company
    metadata, not arbitrary search-result text.
    """
    if not isinstance(title, str):
        raise ValueError("Headline must be text.")

    if not isinstance(company_name, str) or not company_name.strip():
        raise ValueError("Company name is required.")

    text = _normalize(title)

    if not text:
        return RelevanceResult("unmatched", "Empty headline.")

    if _contains(text, company_name):
        return RelevanceResult(
            "likely",
            "Exact company name appears in headline.",
            (company_name,),
        )

    valid_aliases = [
        alias
        for alias in aliases
        if isinstance(alias, str) and len(alias.strip()) >= 3
    ]

    matched_aliases = [
        alias for alias in valid_aliases if _contains(text, alias)
    ]

    if not matched_aliases:
        return RelevanceResult(
            "unmatched",
            "No reviewed company name or alias found.",
        )

    matched_distinctive = [
        term
        for term in distinctive_terms
        if isinstance(term, str)
        and len(term.strip()) >= 3
        and _contains(text, term)
    ]

    if matched_distinctive:
        return RelevanceResult(
            "likely",
            "Company alias and distinctive context appear together.",
            tuple(matched_aliases + matched_distinctive),
        )

    matched_market = [
        term for term in MARKET_TERMS if _contains(text, term)
    ]

    if matched_market:
        return RelevanceResult(
            "needs_review",
            "Company alias and market terminology appear; "
            "identity is not independently confirmed.",
            tuple(matched_aliases + matched_market),
        )

    return RelevanceResult(
        "unmatched",
        "Ambiguous company alias without supporting context.",
        tuple(matched_aliases),
    )
