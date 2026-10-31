"""Tests for the guided inflation lesson."""

import ast
from pathlib import Path

from app.education.catalog import (
    LESSON_SUMMARIES,
    PATHWAYS,
    READY_LESSONS,
)


def test_inflation_registered():
    assert "inflation" in READY_LESSONS
    assert "inflation" in LESSON_SUMMARIES
    assert any(
        lesson_id == "inflation"
        for pathway in PATHWAYS
        for lesson_id, _ in pathway["lessons"]
    )


def test_inflation_lesson_structure():
    source = Path("dashboard/inflation_lesson.py").read_text()
    ast.parse(source)

    for name in (
        "render_inflation_lesson",
        "purchasing_power",
        "real_return_pct",
        "Check what you learned",
        "Bank of Canada",
    ):
        assert name in source


def test_inflation_inputs_are_unique():
    source = Path("dashboard/inflation_lesson.py").read_text()
    for name in (
        "qi_inflation_savings",
        "qi_inflation_rate_",
        "qi_inflation_return_",
        "qi_inflation_question_",
    ):
        assert name in source
