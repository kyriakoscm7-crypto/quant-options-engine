"""Synthetic accounting fixture; never imported by production routing."""
from app.intelligence.fundamental_factors import CONCEPTS


def payload():
    facts = {}
    for metric, (unit, tags) in CONCEPTS.items():
        rows = []
        for year, revenue in [(2023, 100), (2024, 110), (2025, 121)]:
            values = dict(revenue=revenue, operating_income=revenue * (.1 + (year - 2023) * .02),
                          income=10, cfo=20, capex=5, shares=100, assets=200, liabilities=80)
            row = dict(val=values[metric] * (1_000_000 if unit == 'USD' else 1), end=f'{year}-12-31', filed=f'{year + 1}-02-01',
                       form='10-K', accn=f'0000000001-{year % 100:02d}-000001')
            if metric == 'shares':
                row.update(filed='2026-02-01', accn='0000000001-25-000001')
            if metric not in {'assets', 'liabilities'}:
                row['start'] = f'{year}-01-01'
            rows.append(row)
        facts[tags[0]] = {'units': {unit: rows}}
    return {'cik': 1, 'facts': {'us-gaap': facts}}

