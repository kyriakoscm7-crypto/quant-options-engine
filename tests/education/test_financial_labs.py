"""Check the added interactive lessons match the supported model domain."""

import ast
from pathlib import Path

from app.education.catalog import LESSON_SUMMARIES, PATHWAYS, READY_LESSONS
from app.education.financial_models import compound_growth, credit_card_payoff


def test_new_lessons_listed_and_available():
    available = {lesson_id for p in PATHWAYS for lesson_id, _ in p["lessons"]}
    assert {"growth", "credit"} <= READY_LESSONS <= available
    assert {"growth", "credit"} <= set(LESSON_SUMMARIES)


def test_growth_month_end_contribution_example():
    points = compound_growth(5000, 250, 5, 20)
    assert points[0].balance == 5000
    assert len(points) == 21
    assert points[-1].contributed == 65000
    assert points[-1].balance > points[-1].contributed


def test_debt_extra_payment_reduces_cost():
    normal = credit_card_payoff(3000, 20, 150)
    extra = credit_card_payoff(3000, 20, 250)
    assert extra.months < normal.months
    assert extra.interest_paid < normal.interest_paid


def test_labs_are_valid_python_and_have_both_ids():
    source = Path("dashboard/financial_labs.py").read_text()
    ast.parse(source)
    for token in ('qi-growth-v2', 'qi-debt-v2', 'render_compound_growth', 'render_credit_card'):
        assert token in source
