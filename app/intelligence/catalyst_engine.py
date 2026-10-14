"""Explainable headline-level catalyst detection.

These labels describe potential implications, not predicted returns.
Headline text alone cannot establish the full context of an event.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Catalyst:
    category: str
    direction: str
    matched_terms: tuple[str, ...]
    explanation: str


RULES = (
    (
        "Earnings",
        "Potentially Positive",
        ("beats earnings", "earnings beat", "beats estimates",
         "raises guidance", "profit surges"),
        "The headline suggests stronger-than-expected financial results.",
    ),
    (
        "Earnings",
        "Potentially Negative",
        ("misses earnings", "earnings miss", "misses estimates",
         "cuts guidance", "profit plunges"),
        "The headline suggests weaker-than-expected financial results.",
    ),
    (
        "Regulation",
        "Potentially Negative",
        ("regulatory investigation", "antitrust lawsuit",
         "sec investigation", "faces lawsuit", "fined by"),
        "The headline suggests possible legal or regulatory risk.",
    ),
    (
        "Business Development",
        "Potentially Positive",
        ("wins contract", "secures contract", "announces partnership",
         "major partnership"),
        "The headline suggests a potentially favorable business development.",
    ),
    (
        "Corporate Event",
        "Uncertain",
        ("initial public offering", "plans ipo", "files for ipo",
         "stock split", "merger announcement"),
        "The headline describes an event whose market impact is uncertain.",
    ),
    (
        "Product",
        "Uncertain",
        ("launches new product", "unveils new product",
         "announces new product"),
        "A product announcement may affect expectations, but direction is uncertain.",
    ),
)


def analyze_headline(headline: str) -> list[Catalyst]:
    """Return every rule matching the supplied headline."""

    if not isinstance(headline, str):
        raise TypeError("headline must be a string")

    normalized = " ".join(headline.casefold().split())
    findings = []

    for category, direction, terms, explanation in RULES:
        matches = tuple(term for term in terms if term in normalized)

        if matches:
            findings.append(
                Catalyst(
                    category=category,
                    direction=direction,
                    matched_terms=matches,
                    explanation=explanation,
                )
            )

    return findings
