import ast
from pathlib import Path

from app.education.catalog import LESSON_SUMMARIES, PATHWAYS, READY_LESSONS


def test_paycheque_registered():
    assert "paycheque" in READY_LESSONS
    assert "paycheque" in LESSON_SUMMARIES
    assert any(
        lid == "paycheque"
        for path in PATHWAYS
        for lid, _ in path["lessons"]
    )

def test_paycheque_lesson_valid():
    source = Path("dashboard/paycheque_lesson.py").read_text()
    ast.parse(source)
    assert "render_paycheque" in source
    assert "Payroll Deductions Calculator" in source
    assert "fictional" in source.lower()

def test_paycheque_uses_unique_control_keys():
    source = Path("dashboard/paycheque_lesson.py").read_text()
    for key in ("qi_pay_salary", "qi_pay_frequency", "qi_pay_question_"):
        assert key in source
