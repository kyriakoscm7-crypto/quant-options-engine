"""ETF lesson registration and integrity tests."""
import ast
from pathlib import Path

from app.education.catalog import LESSON_SUMMARIES, READY_LESSONS


def test_etf_is_ready():
    assert "etfs" in READY_LESSONS
    assert "etfs" in LESSON_SUMMARIES


def test_etf_lesson_has_expected_components():
    source = Path("dashboard/etf_lesson.py").read_text()
    ast.parse(source)
    for token in (
        "render_etf_lesson",
        "fund_overlap",
        "portfolio_exposure",
        "concentration_index",
        "annual_fee_cost",
        "Check your understanding",
    ):
        assert token in source
