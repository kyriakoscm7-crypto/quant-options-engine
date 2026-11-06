"""Independent arithmetic expectations and explicit same-source limits."""
from copy import deepcopy

import pytest

from app.intelligence.research_checks import internal_agreement, pattern_diagnostics


def test_omission_diagnostic_manual_means_is_not_a_new_score():
    report = {'archetypes': {'pattern': {'score': 50, 'factors': ('a', 'b', 'c')}},
              'scores': {'a': 0, 'b': 50, 'c': 100}}
    before = deepcopy(report)
    result = pattern_diagnostics(report, 'pattern')
    assert result['omission_min'] == 25
    assert result['omission_max'] == 75
    assert result['at_anchor'] == ['a', 'c']
    assert [r['Remaining mean / 100'] for r in result['omissions']] == [75, 50, 25]
    assert report == before
    report['archetypes']['pattern']['score'] = None
    assert pattern_diagnostics(report, 'pattern')['omission_min'] is None


@pytest.mark.parametrize('change,status', [({}, 'agrees'), ({'value': 101}, 'conflict'),
    ({'unit': 'EUR'}, 'not comparable'), ({'start': '2025-02-01'}, 'not comparable'),
    ({'tag': 'SalesRevenueNet'}, 'not comparable'), ({'accession': 'different'}, 'not comparable')])
def test_internal_paths_compare_only_identical_contexts(change, status):
    fact = dict(value=100, unit='USD', start='2025-01-01', end='2025-12-31',
                tag='Revenues', accession='0000000001-25-000001')
    report = {'research': {'history': [{'observations': {'revenue': fact}}]},
              'health': {'observations': {'revenue': {**fact, **change}}}}
    checks = internal_agreement(report)
    assert checks[0]['Status'] == status
    assert all(r['Status'] == 'not comparable' for r in checks[1:])
    assert 'independent' not in checks[0]


def test_missing_report_is_not_treated_as_agreement():
    assert all(r['Status'] == 'not comparable' for r in internal_agreement({}))
