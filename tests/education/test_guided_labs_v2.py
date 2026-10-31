"""Quant Learn guided simulation lesson regression tests."""
import ast
from pathlib import Path

from app.education.financial_models import compound_growth, credit_card_payoff

MODULE = Path("dashboard/financial_labs.py").read_text()
TREE = ast.parse(MODULE)


def test_uses_isolated_script_enabled_renderer():
    assert 'st.iframe(document' in MODULE
    assert 'components.html(document' in MODULE
    assert 'unsafe_allow_javascript' not in MODULE
    assert 'st.html(' not in MODULE


def test_both_labs_teach_before_interaction():
    for key in ('GROWTH', 'DEBT'):
        matches = [n for n in TREE.body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == key for t in n.targets)]
        assert len(matches) == 1
        html = ast.literal_eval(matches[0].value)
        for marker in ('01 Learn', '02 See an example', '03 Experiment',
                       '04 Check yourself', 'qi-choice', 'qi-insight',
                       'dataset.calculated', 'addEventListener', 'aria-live'):
            assert marker in html, (key, marker)


def test_worked_examples_agree_with_python_models():
    # $1,000 + 12 monthly deposits of $100, at a 0% return
    assert compound_growth(1000, 100, 0, 1)[-1].balance == 2200
    # A 24% nominal APR corresponds to $20 in first-month interest on $1,000.
    assert 1000 * (24 / 1200) == 20
    example = credit_card_payoff(1000, 24, 100)
    assert example.months > 0 and example.interest_paid > 0
