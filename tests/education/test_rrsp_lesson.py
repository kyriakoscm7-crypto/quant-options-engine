"""Registration and structure checks for the RRSP lesson."""
import ast
from pathlib import Path

from app.education.catalog import LESSON_SUMMARIES, READY_LESSONS


def test_rrsp_is_ready():
    assert "rrsp" in READY_LESSONS
    assert "rrsp" in LESSON_SUMMARIES


def test_rrsp_lesson_is_valid():
    source = Path("dashboard/rrsp_lesson.py").read_text()
    ast.parse(source)
    for phrase in (
        "render_rrsp_comparison",
        "compare_accounts",
        "Check your understanding",
        "withdrawal",
    ):
        assert phrase in source
