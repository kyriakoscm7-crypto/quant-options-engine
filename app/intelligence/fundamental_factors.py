"""Annual issuer-fact research signals, not valuation or expected-return models.

Scores use fixed clipped anchors, not sample percentiles. Latest-known revisions
are visible; an as-of cutoff filters filings but cannot recreate historical feeds.
"""
import math
from datetime import date

from app.intelligence.sec_filings import ACCESSION_PATTERN

CONCEPTS = {
    'revenue': ('USD', ('RevenueFromContractWithCustomerExcludingAssessedTax', 'Revenues', 'SalesRevenueNet')),
    'operating_income': ('USD', ('OperatingIncomeLoss',)),
    'income': ('USD', ('NetIncomeLoss',)),
    'cfo': ('USD', ('NetCashProvidedByUsedInOperatingActivities',)),
    'capex': ('USD', ('PaymentsToAcquirePropertyPlantAndEquipment',)),
    'shares': ('shares', ('WeightedAverageNumberOfDilutedSharesOutstanding',)),
    'assets': ('USD', ('Assets',)),
    'liabilities': ('USD', ('Liabilities',)),
}
INSTANT = {'assets', 'liabilities'}
# Lower/upper anchors map linearly to 0/100; bounds also winsorize outliers.
ANCHORS = {
    'revenue_cagr': (-.10, .20, 1), 'margin_change': (-.05, .05, 1),
    'operating_margin': (0, .30, 1), 'fcf_margin': (0, .25, 1),
    'cash_conversion': (.5, 1.5, 1), 'liabilities_assets': (.2, .9, -1),
    'share_cagr': (-.05, .05, -1), 'earnings_consistency': (0, 1, 1),
}
ARCHETYPES = {
    'Quality compounders': ('revenue_cagr', 'operating_margin', 'earnings_consistency', 'liabilities_assets'),
    'Improving fundamentals': ('margin_change', 'revenue_cagr', 'share_cagr'),
    'Cash generators': ('fcf_margin', 'cash_conversion', 'liabilities_assets'),
    'Turnarounds to investigate': ('margin_change', 'fcf_margin', 'revenue_cagr'),
}


def annual_evidence(payload, cik, *, as_of):
    """Conservative standard-tag annual observations; reject ambiguous contexts."""
    if str(payload.get('cik', '')).lstrip('0') != str(cik).lstrip('0'):
        raise ValueError('Company facts CIK mismatch')
    root = payload.get('facts', {})
    root = root.get('us-gaap', {}) if isinstance(root, dict) else {}
    root = root if isinstance(root, dict) else {}
    series, issues = {}, []
    for metric, (unit, tags) in CONCEPTS.items():
        candidates = {}
        for tag in tags:
            concept = root.get(tag, {})
            units = concept.get('units', {}) if isinstance(concept, dict) else {}
            rows = units.get(unit, []) if isinstance(units, dict) else []
            for row in rows if isinstance(rows, list) else []:
                try:
                    if not isinstance(row, dict):
                        continue
                    end, filed = date.fromisoformat(row['end']), date.fromisoformat(row['filed'])
                    val = row['val']
                    if isinstance(val, bool) or not isinstance(val, (float, int)) or not math.isfinite(val):
                        continue
                    if not end <= filed <= as_of or row['form'] not in {'10-K', '10-K/A'}:
                        continue
                    if not ACCESSION_PATTERN.fullmatch(row['accn']):
                        continue
                    start = row.get('start')
                    if metric in INSTANT:
                        if start:
                            continue
                    elif not 330 <= (end - date.fromisoformat(start)).days <= 380:
                        continue
                    obs = dict(metric=metric, value=val, unit=unit, tag=tag, start=start,
                               end=end.isoformat(), filed=filed.isoformat(), accession=row['accn'],
                               url=f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{row['accn'].replace('-', '')}/")
                    candidates.setdefault(obs['end'], []).append(obs)
                except (KeyError, TypeError, ValueError):
                    continue
        series[metric] = {}
        for end, rows in candidates.items():
            latest = max(r['filed'] for r in rows)
            selected = [r for r in rows if r['filed'] == latest]
            if len({(r['value'], r['start'], r['accession']) for r in selected}) != 1:
                issues.append(f'{metric} {end}: conflicting latest contexts excluded')
                continue
            series[metric][end] = selected[0]
            if len({r['value'] for r in rows}) > 1:
                issues.append(f'{metric} {end}: revised values; latest known filing used')
    return series, issues


def compatible(*rows):
    return all(rows) and len({(r['start'], r['end'], r['accession']) for r in rows}) == 1


def factor_research(payload, cik, *, sic=None, as_of=None):
    as_of = as_of or date.today()
    series, issues = annual_evidence(payload, cik, as_of=as_of)
    periods = sorted({end for key, values in series.items() if key not in INSTANT for end in values})[-5:]
    history = []
    for end in periods:
        obs = {key: values.get(end) for key, values in series.items()}
        def ratio(a, b):
            x, y = obs[a], obs[b]
            value = x['value'] / y['value'] if compatible(x, y) and y['value'] > 0 else None
            return value if value is not None and math.isfinite(value) else None
        cfo, capex, rev = obs['cfo'], obs['capex'], obs['revenue']
        fcf = cfo['value'] - capex['value'] if compatible(cfo, capex) and capex['value'] >= 0 else None
        fcf_margin = fcf / rev['value'] if fcf is not None and compatible(cfo, capex, rev) and rev['value'] > 0 else None
        if fcf is not None and not math.isfinite(fcf):
            fcf = None
        if fcf_margin is not None and not math.isfinite(fcf_margin):
            fcf_margin = None
        history.append(dict(period=end, observations=obs, operating_margin=ratio('operating_income', 'revenue'),
                            fcf=fcf, fcf_margin=fcf_margin, cash_conversion=ratio('cfo', 'income'),
                            liabilities_assets=ratio('liabilities', 'assets')))
    latest = history[-1] if history else {}
    def contiguous(rows):
        return len(rows) >= 3 and all(rows) and all(
            350 <= (date.fromisoformat(b['end']) - date.fromisoformat(a['end'])).days <= 380
            and 0 <= (date.fromisoformat(b['start']) - date.fromisoformat(a['end'])).days <= 14
            for a, b in zip(rows, rows[1:]))

    # Trends need a contiguous annual sequence, a single concept and comparable durations.
    def trend(metric, rows=None):
        rows = [h['observations'][metric] for h in history] if rows is None else rows
        if not contiguous(rows):
            return None
        if len({r['tag'] for r in rows}) != 1 or any(r['value'] <= 0 for r in rows):
            return None
        if any(not 330 <= (date.fromisoformat(b['end']) - date.fromisoformat(a['end'])).days <= 400
               or abs((date.fromisoformat(b['end']) - date.fromisoformat(b['start'])).days -
                      (date.fromisoformat(a['end']) - date.fromisoformat(a['start'])).days) > 14
               for a, b in zip(rows, rows[1:])):
            return None
        years = (date.fromisoformat(rows[-1]['end']) - date.fromisoformat(rows[0]['end'])).days / 365.2425
        exponent = (math.log(rows[-1]['value']) - math.log(rows[0]['value'])) / years
        return math.expm1(exponent) if exponent < 700 else None
    consecutive = len(periods) >= 3 and all(330 <= (date.fromisoformat(b) - date.fromisoformat(a)).days <= 400 for a, b in zip(periods, periods[1:]))
    margins = [h['operating_margin'] for h in history]
    incomes = [h['observations']['income'] for h in history]
    margin_periods_compatible = contiguous([h['observations']['revenue'] for h in history])
    margin_tags_consistent = all(len({h['observations'][k]['tag'] for h in history if h['observations'][k]}) == 1 for k in ('revenue', 'operating_income'))
    # Share counts from different filings may use different split bases. Use only
    # the contiguous comparative suffix in the latest share observation's filing;
    # never infer a split ratio from a numerical jump or stitch filing bases.
    share_rows = []
    latest_shares = latest.get('observations', {}).get('shares')
    if latest_shares:
        for h in reversed(history):
            row = h['observations']['shares']
            if not row or row['accession'] != latest_shares['accession']:
                break
            share_rows.insert(0, row)
    share_growth = trend('shares', share_rows)
    if share_growth is None and any(h['observations']['shares'] for h in history):
        issues.append('Share CAGR unavailable: need at least three consecutive annual share observations in one filing; cross-filing split bases are not inferred.')
    share_window = dict(start=share_rows[0]['end'], end=share_rows[-1]['end'],
                        observations=len(share_rows), accession=latest_shares['accession']) if share_growth is not None else None
    factors = dict(revenue_cagr=trend('revenue'), share_cagr=share_growth,
                   margin_change=margins[-1] - margins[0] if consecutive and margin_periods_compatible and margin_tags_consistent and all(x is not None for x in margins) else None,
                   earnings_consistency=sum(x['value'] > 0 for x in incomes) / len(incomes) if contiguous(incomes) else None,
                   **{key: latest.get(key) for key in ('operating_margin', 'fcf_margin', 'cash_conversion', 'liabilities_assets')})
    try:
        code = int(sic)
        restricted = 6000 <= code <= 6999 or 4900 <= code <= 4999
        sector = 'Financial / real estate or utility: generic model not applicable' if restricted else f'SIC {code}: generic nonfinancial model; accounting comparability unverified'
        applicable = 100 <= code <= 9999 and not restricted
    except (ValueError, TypeError, OverflowError):
        sector, applicable = 'SIC unavailable: sector applicability unverified', False
    recent = bool(periods) and 0 <= (as_of - date.fromisoformat(periods[-1])).days <= 550
    scores = {}
    for key, value in factors.items():
        lo, hi, direction = ANCHORS[key]
        scaled = min(1., max(0., (value - lo) / (hi - lo))) if value is not None else None
        scores[key] = (scaled if direction == 1 else 1 - scaled) * 100 if scaled is not None else None
    archetypes = {}
    for name, keys in ARCHETYPES.items():
        available = sum(factors[k] is not None for k in keys)
        score = sum(scores[k] for k in keys) / len(keys) if available == len(keys) and applicable and recent else None
        reasons = [f'Missing {k}' for k in keys if factors[k] is None]
        if not applicable:
            reasons.append('Sector model not applicable or unverified')
        if not recent:
            reasons.append('Missing or stale annual period')
        if name == 'Turnarounds to investigate' and not (contiguous(incomes) and incomes[0]['value'] < 0 < incomes[-1]['value']):
            score = None
            reasons.append('No comparable observed loss-to-profit sequence')
        archetypes[name] = dict(score=score, coverage=f'{available}/{len(keys)}', factors=keys, reasons=reasons)
    risks = ['Annual accounting signals do not measure valuation, competitive durability or investment returns.']
    if factors['cash_conversion'] is not None and factors['cash_conversion'] < 1:
        risks.append('Operating cash trails positive net income; investigate working capital and noncash items.')
    if share_window is None:
        risks.append('Share-count comparability unverified; no dilution trend is inferred across filing bases.')
    if factors['share_cagr'] is not None and factors['share_cagr'] > 0:
        risks.append('Diluted weighted-average shares increased; investigate dilution and per-share economics.')
    if latest.get('fcf') is not None and latest['fcf'] < 0:
        risks.append('Reported operating cash did not cover PP&E purchases; inspect investment cycles and funding.')
    if issues:
        risks.append('Revisions or conflicting contexts exist; inspect excluded observations before relying on a pattern.')
    if not recent:
        risks.append('Latest annual period missing or older than 550 days; no ranking.')
    return dict(as_of=as_of.isoformat(), period=periods[-1] if periods else None, history=history,
                factors=factors, scores=scores, archetypes=archetypes, sector=sector,
                factor_windows={'share_cagr': share_window},
                issues=issues, risks=risks, coverage=f'{sum(v is not None for v in factors.values())}/{len(factors)}',
                uncertainty='Single issuer source; latest-known restatements; no point-in-time backtest or peer percentile.')


def operating_scenario(revenue, operating_income, *, revenue_change, margin_change_pp):
    """Mechanical one-period sensitivity: user shocks, no forecast or valuation."""
    values = (revenue, operating_income, revenue_change, margin_change_pp)
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
        raise ValueError('Finite numeric scenario inputs required')
    if revenue <= 0 or not -1 <= revenue_change <= 2 or not -50 <= margin_change_pp <= 50:
        raise ValueError('Scenario inputs outside supported bounds')
    stressed_revenue = revenue * (1 + revenue_change)
    margin = operating_income / revenue + margin_change_pp / 100
    income = stressed_revenue * margin
    if not all(math.isfinite(x) for x in (stressed_revenue, margin, income)):
        raise ValueError('Scenario overflow')
    return dict(revenue=stressed_revenue, operating_margin=margin, operating_income=income,
                income_change=income - operating_income)
