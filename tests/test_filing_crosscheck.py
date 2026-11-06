"""Original-document checks: scale, units, context, identity and failure boundaries."""
from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from app.intelligence.company_identity import CompanyIdentity
from app.intelligence.discover_sec import SecGateway
from app.intelligence.filing_crosscheck import check_original_filing, compare_filing

CIK = '0000000001'
ACC = '0000000001-26-000001'


def document(value='100', attrs='', context='', unit='iso4217:USD', end='2025-12-31', identifier=CIK):
    return f'''<html><ix:header><ix:resources>
    <xbrli:context id="annual"><xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">{identifier}</xbrli:identifier>{context}</xbrli:entity>
    <xbrli:period><xbrli:startDate>2025-01-01</xbrli:startDate><xbrli:endDate>{end}</xbrli:endDate></xbrli:period></xbrli:context>
    <xbrli:unit id="usd"><xbrli:measure>{unit}</xbrli:measure></xbrli:unit>
    </ix:resources></ix:header><ix:nonFraction name="us-gaap:Revenues" contextRef="annual" unitRef="usd" decimals="0" {attrs}>{value}</ix:nonFraction></html>'''


def observation(**changes):
    return dict(metric='revenue', tag='Revenues', value=100, unit='USD', start='2025-01-01',
                end='2025-12-31', accession=ACC, **changes)


def status(html, obs=None):
    return compare_filing(html, CIK, ACC, [obs or observation()])[0]['Status']


def test_exact_scale_sign_rounding_and_excluded_markup():
    assert status(document()) == 'exact agreement'
    assert status(document('0.1', 'scale="3"')) == 'exact agreement'
    assert status(document('<span>100</span><ix:exclude>extra prose</ix:exclude>')) == 'exact agreement'
    obs = observation()
    obs['value'] = -100
    assert status(document('100', 'sign="-"'), obs) == 'exact agreement'
    obs['value'] = 100.4
    assert status(document(), obs) == 'within reported rounding'
    obs['value'] = 100.6
    assert status(document(), obs) == 'discrepancy'


@pytest.mark.parametrize('html', [document(unit='iso4217:EUR'), document(identifier='0000000002'),
    document(end='2024-12-31'), document('100', 'format="ixt:num-comma-decimal"'),
    document('100', 'scale="999"'), document('NaN'), document('1,00'),
    document(context='<xbrli:segment><xbrldi:explicitMember>segment</xbrldi:explicitMember></xbrli:segment>'),
    document('100', 'xsi:nil="true"'), document('100', 'decimals="999"'), document('100', 'sign="+"')])
def test_unsupported_or_incompatible_never_reports_agreement(html):
    assert status(html) == 'not comparable'


def test_conflicting_duplicates_or_accession_mismatch():
    html = document().replace('</html>', '<ix:nonFraction name="us-gaap:Revenues" contextRef="annual" unitRef="usd" decimals="0">101</ix:nonFraction></html>')
    assert status(html) == 'conflicting filing facts'
    obs = observation()
    obs['accession'] = '0000000001-26-000002'
    assert status(document(), obs) == 'not comparable'


def test_duplicate_context_ids_fail_closed():
    html = document().replace('</html>', document(identifier='0000000002') + '</html>')
    assert status(html) == 'not comparable'


def test_bounded_gateway_filing_fetch_cache_and_url_guards():
    response = Mock(status_code=200)
    response.iter_content.return_value = [document().encode()]
    get = Mock(return_value=response)
    gateway = SecGateway('Quant Intelligence test@operator.org', get=get, sleep=lambda _: None)
    result = gateway.fetch('filing', CIK, accession=ACC, document='annual-2025.htm')
    assert result['data'] == document()
    assert get.call_args.args[0] == 'https://www.sec.gov/Archives/edgar/data/1/000000000126000001/annual-2025.htm'
    assert get.call_args.kwargs['allow_redirects'] is False
    assert gateway.fetch('filing', CIK, accession=ACC, document='annual-2025.htm') == result
    assert get.call_count == 1
    response.close.assert_called_once()
    for name in ('../evil.htm', 'https://evil.test/a.htm', 'a.htm?x=y', 'report.xml', 'a%2f.htm'):
        with pytest.raises(ValueError):
            gateway.fetch('filing', CIK, accession=ACC, document=name)
    assert get.call_count == 1


def test_filing_fetch_preserves_cooldown():
    get = Mock(return_value=Mock(status_code=429, headers={}))
    gateway = SecGateway('Quant Intelligence test@operator.org', get=get, clock=lambda: 0, sleep=lambda _: None)
    with pytest.raises(RuntimeError):
        gateway.fetch('filing', CIK, accession=ACC, document='annual.htm')
    with pytest.raises(RuntimeError, match='cooldown'):
        gateway.fetch('companyfacts', CIK)
    assert get.call_count == 1


def test_original_check_uses_normalized_filing_and_preserves_scoring_inputs():
    from copy import deepcopy

    gateway = Mock()
    gateway.fetch.return_value = {'data': document(), 'url': 'https://www.sec.gov/original',
                                  'retrieved_at': datetime.now(UTC).isoformat()}
    report = {'company': CompanyIdentity('QA', 'Synthetic', CIK),
              'filings': [{'form': '10-K', 'accession': ACC, 'filing_date': '2026-02-01',
                           'url': 'https://www.sec.gov/Archives/edgar/data/1/000000000126000001/annual.htm'}],
              'research': {'history': [{'observations': {'revenue': observation()}}]}}
    before = deepcopy(report)
    checked = check_original_filing(gateway, report)
    assert checked['rows'][0]['Status'] == 'exact agreement'
    assert report == before
    gateway.fetch.assert_called_once_with('filing', CIK, accession=ACC, document='annual.htm')
    report['filings'] = []
    with pytest.raises(ValueError, match='No recent annual filing'):
        check_original_filing(gateway, report)


def test_share_and_instant_units_and_million_scale():
    obs = observation()
    obs.update(metric='shares', tag='WeightedAverageNumberOfDilutedSharesOutstanding', value=24514000000, unit='shares')
    html = document('24,514', 'scale="6"').replace('us-gaap:Revenues', 'us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding').replace('iso4217:USD', 'xbrli:shares')
    assert status(html, obs) == 'exact agreement'
    obs.update(metric='assets', tag='Assets', value=100, unit='USD', start=None)
    html = document().replace('us-gaap:Revenues', 'us-gaap:Assets').replace('<xbrli:startDate>2025-01-01</xbrli:startDate><xbrli:endDate>2025-12-31</xbrli:endDate>', '<xbrli:instant>2025-12-31</xbrli:instant>')
    assert status(html, obs) == 'exact agreement'


def test_large_or_wrong_type_document_rejected_without_parsing():
    for content in (None, b'<html/>', 'x' * 25000001):
        with pytest.raises(ValueError):
            compare_filing(content, CIK, ACC, [observation()])
