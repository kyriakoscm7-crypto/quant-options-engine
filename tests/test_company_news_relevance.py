"""Headline relevance tests with ambiguity and collision cases."""

import pytest

from app.intelligence.company_news_relevance import (
    classify_headline,
)


def apple(title):
    return classify_headline(
        title,
        "Apple Inc.",
        aliases=("Apple",),
        distinctive_terms=("MacBook", "iPhone", "iPad"),
    )


def test_exact_legal_name():
    result = apple("Apple Inc. announces quarterly results")
    assert result.status == "likely"


def test_distinctive_product_context():
    result = apple("Apple announces new MacBook models")
    assert result.status == "likely"


def test_ambiguous_market_context_needs_review():
    result = apple("Apple shares rise after product launch")
    assert result.status == "needs_review"


def test_farming_story_is_not_matched():
    result = apple("Apple farmers celebrate record harvest")
    assert result.status == "unmatched"


def test_word_boundaries_prevent_partial_matches():
    result = apple("Pineapple producers expand operations")
    assert result.status == "unmatched"


def test_company_without_alias_does_not_guess():
    result = classify_headline(
        "New AI company reports strong growth",
        "NVIDIA Corporation",
    )
    assert result.status == "unmatched"


def test_exact_name_for_another_company():
    result = classify_headline(
        "Palantir Technologies announces earnings",
        "Palantir Technologies",
    )
    assert result.status == "likely"


def test_ambiguous_block_name():
    result = classify_headline(
        "Construction block shortages continue",
        "Block Inc.",
        aliases=("Block",),
    )
    assert result.status == "unmatched"


def test_short_alias_is_ignored():
    result = classify_headline(
        "AI stocks rally",
        "Example Corporation",
        aliases=("AI",),
    )
    assert result.status == "unmatched"


def test_missing_company_is_rejected():
    with pytest.raises(ValueError):
        classify_headline("Some headline", "")


def test_empty_headline():
    result = apple("")
    assert result.status == "unmatched"


def test_case_insensitive_matching():
    result = apple("APPLE INC. REPORTS RESULTS")
    assert result.status == "likely"
