"""Transparent diagnostics, separate from factor scoring and source independence."""
from math import fsum


def pattern_diagnostics(research, archetype):
    """Leave-one-factor-out sensitivity; never a confidence interval or new score."""
    pattern = research['archetypes'][archetype]
    keys = pattern['factors']
    values = [research['scores'].get(k) for k in keys]
    capped = [k for k, value in zip(keys, values) if value in (0, 100)]
    if pattern['score'] is None or len(values) < 2 or any(v is None for v in values):
        return {'omission_min': None, 'omission_max': None, 'at_anchor': capped, 'omissions': []}
    total = fsum(values)
    omissions = [{'Omitted factor': k, 'Remaining mean / 100': (total - v) / (len(values) - 1)}
                 for k, v in zip(keys, values)]
    means = [row['Remaining mean / 100'] for row in omissions]
    return {'omission_min': min(means), 'omission_max': max(means),
            'at_anchor': capped, 'omissions': omissions}


def internal_agreement(report):
    """Compare two extraction paths only when metric, context and units match.

    Both paths use the same SEC Company Facts payload. Agreement can catch
    extraction inconsistency; it is explicitly NOT independent corroboration.
    """
    research = report.get('research') or {}
    history = research.get('history') or []
    latest = history[-1]['observations'] if history else {}
    health = (report.get('health') or {}).get('observations', {})
    checks = []
    for key, alias in (('revenue', 'revenue'), ('income', 'income'), ('cfo', 'operating_cash'),
                       ('assets', 'assets'), ('liabilities', 'liabilities')):
        a, b = latest.get(key), health.get(alias)
        context = ('start', 'end', 'unit', 'accession', 'tag')
        comparable = bool(a and b and all(a.get(k) and b.get(k) for k in ('end', 'unit', 'accession', 'tag'))
                          and all(a.get(k) == b.get(k) for k in context))
        status = ('agrees' if a['value'] == b['value'] else 'conflict') if comparable else 'not comparable'
        checks.append({'Metric': key, 'Status': status,
                       'Research value': a['value'] if a else None,
                       'Health value': b['value'] if b else None})
    return checks
