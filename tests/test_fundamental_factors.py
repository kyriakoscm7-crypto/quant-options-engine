"""Synthetic, independently specified accounting and boundary cases."""
from copy import deepcopy
from datetime import date

import pytest

from app.intelligence.fundamental_factors import (
    CONCEPTS,
    factor_research,
    operating_scenario,
)

ASOF = date(2026, 11, 5)


def payload():
    facts = {}
    for metric, (unit, tags) in CONCEPTS.items():
        rows = []
        for year, revenue in [(2023, 100), (2024, 110), (2025, 121)]:
            values = dict(revenue=revenue, operating_income=revenue * (.1 + (year - 2023) * .02),
                          income=10, cfo=20, capex=5, shares=100, assets=200, liabilities=80)
            row = dict(val=values[metric], end=f'{year}-12-31', filed=f'{year + 1}-02-01',
                       form='10-K', accn=f'0000000001-{year % 100:02d}-000001')
            if metric not in {'assets', 'liabilities'}:
                row['start'] = f'{year}-01-01'
            rows.append(row)
        facts[tags[0]] = {'units': {unit: rows}}
    return {'cik': 1, 'facts': {'us-gaap': facts}}


def rows(data, metric):
    unit, tags = CONCEPTS[metric]
    return data['facts']['us-gaap'][tags[0]]['units'][unit]


def research(data=None, **kwargs):
    return factor_research(data or payload(), '0000000001', sic='3571', as_of=ASOF, **kwargs)


def test_known_math_and_explainable_equal_weights():
    r = research()
    assert r['factors']['revenue_cagr'] == pytest.approx(.1, abs=.0001)
    assert r['factors']['margin_change'] == pytest.approx(.04)
    assert r['factors']['fcf_margin'] == pytest.approx(15 / 121)
    assert r['factors']['cash_conversion'] == 2
    assert r['factors']['liabilities_assets'] == .4
    assert r['factors']['share_cagr'] == 0
    assert r['factors']['earnings_consistency'] == 1
    pattern = r['archetypes']['Quality compounders']
    assert pattern['score'] == pytest.approx(sum(r['scores'][k] for k in pattern['factors']) / 4)
    assert r['scores']['cash_conversion'] == 100  # clipped outlier
    assert r['archetypes']['Turnarounds to investigate']['score'] is None


@pytest.mark.parametrize('metric,patch', [
    ('capex', {'val': -5}), ('cfo', {'start': '2025-04-01'}),
    ('capex', {'accn': '0000000001-25-000009'}),
    ('capex', {'val': float('nan')}), ('capex', {'val': True}),
    ('capex', {'filed': '2027-01-01'}), ('capex', {'form': '10-Q'}),
])
def test_incompatible_fcf_never_imputed(metric, patch):
    data = payload()
    rows(data, metric)[-1].update(patch)
    assert research(data)['factors']['fcf_margin'] is None
    assert research(data)['archetypes']['Cash generators']['score'] is None


def test_currency_shares_units_and_missing_period():
    data = payload()
    unit, tags = CONCEPTS['shares']
    data['facts']['us-gaap'][tags[0]]['units']['USD'] = data['facts']['us-gaap'][tags[0]]['units'].pop(unit)
    rows(data, 'revenue').pop(1)
    r = research(data)
    assert r['factors']['share_cagr'] is None
    assert r['factors']['revenue_cagr'] is None


def test_restatement_conflict_cutoff_and_provenance():
    data = payload()
    original = deepcopy(rows(data, 'revenue')[-1])
    rows(data, 'revenue').append({**original, 'val': 150, 'filed': '2026-10-01',
                                'form': '10-K/A', 'accn': '0000000001-26-000002'})
    r = research(data)
    assert r['history'][-1]['observations']['revenue']['value'] == 150
    assert r['factors']['operating_margin'] is None  # no mixing original numerator
    assert any('revised' in i for i in r['issues'])
    early = factor_research(data, 1, sic=3571, as_of=date(2026, 3, 1))
    assert early['history'][-1]['observations']['revenue']['value'] == 121
    rows(data, 'revenue').append({**rows(data, 'revenue')[-1], 'val': 160})
    assert research(data)['history'][-1]['observations']['revenue'] is None


@pytest.mark.parametrize('sic', [None, 'bad', 6021, 6798, 4911])
def test_sector_exceptions_never_rank(sic):
    r = factor_research(payload(), 1, sic=sic, as_of=ASOF)
    assert all(p['score'] is None for p in r['archetypes'].values())


def test_stale_and_no_lookahead():
    r = factor_research(payload(), 1, sic=3571, as_of=date(2030, 1, 1))
    assert all(p['score'] is None for p in r['archetypes'].values())
    early = factor_research(payload(), 1, sic=3571, as_of=date(2025, 1, 1))
    assert early['period'] == '2023-12-31'
    assert early['factors']['revenue_cagr'] is None


def test_tag_switch_no_growth_and_nonpositive_income_no_conversion():
    data = payload()
    tag = CONCEPTS['revenue'][1][0]
    data['facts']['us-gaap']['Revenues'] = {'units': {'USD': [rows(data, 'revenue').pop(0)]}}
    assert tag in data['facts']['us-gaap']
    rows(data, 'income')[-1]['val'] = -1
    r = research(data)
    assert r['factors']['revenue_cagr'] is None
    assert r['factors']['cash_conversion'] is None
    assert r['factors']['earnings_consistency'] == pytest.approx(2 / 3)


def test_scenario_manual_calculation_and_input_bounds():
    result = operating_scenario(100, 20, revenue_change=-.1, margin_change_pp=-5)
    assert result['revenue'] == 90
    assert result['operating_income'] == pytest.approx(13.5)
    assert result['income_change'] == pytest.approx(-6.5)
    assert operating_scenario(100, -20, revenue_change=0, margin_change_pp=0)['operating_income'] == -20
    for value in [float('nan'), float('inf'), True, '10']:
        with pytest.raises(ValueError):
            operating_scenario(100, 20, revenue_change=value, margin_change_pp=0)
    with pytest.raises(ValueError):
        operating_scenario(0, 20, revenue_change=0, margin_change_pp=0)


@pytest.mark.parametrize('metric', ['revenue', 'shares'])
def test_zero_negative_and_extreme_cagr_inputs(metric):
    for value in [0, -1]:
        data = payload()
        rows(data, metric)[0]['val'] = value
        key = 'revenue_cagr' if metric == 'revenue' else 'share_cagr'
        assert research(data)['factors'][key] is None
    data = payload()
    rows(data, metric)[0]['val'] = 1e-300
    rows(data, metric)[-1]['val'] = 1e300
    result = research(data)
    assert all(x is None or 0 <= x <= 100 for x in result['scores'].values())


def test_turnaround_requires_observed_loss_to_profit():
    data = payload()
    rows(data, 'income')[0]['val'] = -10
    r = research(data)
    assert r['archetypes']['Turnarounds to investigate']['score'] is not None
    rows(data, 'income').pop(1)
    assert research(data)['archetypes']['Turnarounds to investigate']['score'] is None


def test_balance_sheet_period_and_identity_guards():
    data = payload()
    rows(data, 'liabilities')[-1]['start'] = '2025-01-01'
    assert research(data)['factors']['liabilities_assets'] is None
    with pytest.raises(ValueError, match='CIK'):
        factor_research(data, 2, sic=3571, as_of=ASOF)


def test_all_missing_has_no_score_and_no_assumptions():
    r = factor_research({'cik': 1}, 1, sic=3571, as_of=ASOF)
    assert r['coverage'] == '0/8'
    assert r['history'] == []
    assert all(p['score'] is None for p in r['archetypes'].values())


def test_duration_mismatch_suppresses_growth():
    data = payload()
    rows(data, 'revenue')[0]['start'] = '2023-02-01'  # still annual, incompatible duration
    assert research(data)['factors']['revenue_cagr'] is None


def test_factor_ui_missing_filter_and_scenario(monkeypatch):
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    monkeypatch.setenv('QI_QA_FACTORS', '1')
    app = AppTest.from_file(str(Path(__file__).parents[1] / 'qa/discover_preview.py')).run()
    app.button[0].click().run()
    assert not app.exception
    before = app.metric[0].value
    app.slider[0].set_value(-20).run()
    assert not app.exception
    assert app.metric[0].value != before
    app.checkbox[0].check().run()
    assert 'QAMISSING' not in app.radio[-1].options
