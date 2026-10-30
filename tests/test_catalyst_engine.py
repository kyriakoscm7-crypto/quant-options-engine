"""Tests for explainable, headline-level catalyst classification."""

import pytest

from app.intelligence.catalyst_engine import analyze_headline


@pytest.mark.parametrize(
    ("headline", "category", "direction"),
    [
        ("Company beats estimates", "Earnings", "Potentially Positive"),
        ("Company cuts guidance", "Earnings", "Potentially Negative"),
        ("Company faces lawsuit", "Regulation", "Potentially Negative"),
        (
            "Company announces partnership",
            "Business Development",
            "Potentially Positive",
        ),
        ("Company files for IPO", "Corporate Event", "Uncertain"),
        ("Company unveils new product", "Product", "Uncertain"),
    ],
)
def test_catalyst_categories(headline, category, direction):
    findings = analyze_headline(headline)

    assert findings
    assert any(
        result.category == category and result.direction == direction
        for result in findings
    )


def test_catalyst_has_display_label():
    finding = analyze_headline("Company beats estimates")[0]

    assert finding.label == "Earnings (Potentially Positive)"
    assert finding.explanation


def test_multiple_catalysts_can_be_reported():
    findings = analyze_headline(
        "Company beats estimates and announces partnership"
    )

    categories = {finding.category for finding in findings}

    assert "Earnings" in categories
    assert "Business Development" in categories


def test_unrecognized_headline_has_no_classification():
    assert analyze_headline("Company provides routine update") == []


def test_invalid_headline_raises_type_error():
    with pytest.raises(TypeError):
        analyze_headline(None)
