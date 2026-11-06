"""On-demand original iXBRL document checks, not independent corroboration.

Parse a narrow numeric subset with stdlib HTMLParser. Unsupported transforms,
entity/dimensional contexts and conflicting duplicates fail closed. Never execute
markup, retrieve embedded resources, infer a value or replace scoring inputs.
"""
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from urllib.parse import urlsplit


class _InlineFacts(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.contexts, self.units, self.facts = {}, {}, []
        self.context = self.unit = self.fact = self.capture = None
        self.excluded = 0
        self.nodes = 0

    @staticmethod
    def _register(mapping, key, value):
        if key:
            mapping[key] = value if key not in mapping or mapping[key] == value else None

    def handle_starttag(self, tag, attrs):
        self.nodes += 1
        if self.nodes > 250_000:
            raise ValueError('Filing structure exceeds limit')
        attrs = dict(attrs)
        if tag == 'xbrli:context':
            self.context = {'id': attrs.get('id'), 'entity': '', 'start': '', 'end': '', 'instant': '', 'dimensioned': False}
        elif self.context is not None:
            fields = {'xbrli:identifier': 'entity', 'xbrli:startdate': 'start',
                      'xbrli:enddate': 'end', 'xbrli:instant': 'instant'}
            if tag in fields:
                self.capture = (tag, fields[tag])
                if tag == 'xbrli:identifier' and attrs.get('scheme') not in {'http://www.sec.gov/CIK', 'https://www.sec.gov/CIK'}:
                    self.context['dimensioned'] = True
            if tag in {'xbrli:segment', 'xbrli:scenario', 'xbrldi:explicitmember', 'xbrldi:typedmember'}:
                self.context['dimensioned'] = True
        if tag == 'xbrli:unit':
            self.unit = {'id': attrs.get('id'), 'measures': [], 'divided': False}
        elif self.unit is not None:
            if tag == 'xbrli:measure':
                self.unit['measures'].append('')
                self.capture = (tag, 'measure')
            if tag == 'xbrli:divide':
                self.unit['divided'] = True
        if tag == 'ix:nonfraction':
            if self.fact is not None:
                self.fact['invalid'] = True
            else:
                self.fact = {'attrs': attrs, 'text': '', 'invalid': False}
        if tag == 'ix:exclude' and self.fact is not None:
            self.excluded += 1

    def handle_endtag(self, tag):
        if self.capture and self.capture[0] == tag:
            self.capture = None
        if tag == 'xbrli:context' and self.context is not None:
            self._register(self.contexts, self.context['id'], self.context)
            self.context = None
        if tag == 'xbrli:unit' and self.unit is not None:
            self._register(self.units, self.unit['id'], self.unit)
            self.unit = None
        if tag == 'ix:exclude' and self.excluded:
            self.excluded -= 1
        if tag == 'ix:nonfraction' and self.fact is not None:
            self.facts.append(self.fact)
            self.fact = None
            self.excluded = 0

    def handle_data(self, data):
        if self.capture:
            field = self.capture[1]
            if field == 'measure' and self.unit is not None:
                self.unit['measures'][-1] += data
            elif self.context is not None:
                self.context[field] += data
        if self.fact is not None and not self.excluded:
            self.fact['text'] += data


def _number(fact):
    attrs = fact['attrs']
    transform = attrs.get('format', '').split(':')[-1].lower()
    if (fact['invalid'] or attrs.get('xsi:nil', '').lower() in {'true', '1'}
            or transform not in {'', 'num-dot-decimal', 'numdotdecimal'}):
        return None
    raw = re.sub(r'\s+', '', fact['text'])
    if len(raw) > 100 or not re.fullmatch(r'-?(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?', raw):
        return None
    try:
        scale = int(attrs.get('scale', '0'))
        if not -12 <= scale <= 12 or attrs.get('sign', '') not in {'', '-'}:
            return None
        value = Decimal(raw.replace(',', '')) * Decimal(10) ** scale
        if attrs.get('sign') == '-':
            if value < 0:
                return None
            value = -value
        precision = attrs.get('decimals', '')
        if precision.upper() == 'INF':
            tolerance = Decimal(0)
        else:
            decimals = int(precision)
            if not -18 <= decimals <= 18:
                return None
            tolerance = Decimal('0.5') * Decimal(10) ** -decimals
        return value, tolerance
    except (InvalidOperation, ValueError, OverflowError):
        return None


def compare_filing(document, cik, accession, observations):
    """Match exact taxonomy/context/unit and classify disagreements explicitly."""
    if not isinstance(document, str) or len(document.encode('utf-8')) > 25_000_000:
        raise ValueError('Invalid or oversized filing document')
    parser = _InlineFacts()
    parser.feed(document)
    parser.close()
    candidates = {}
    for fact in parser.facts:
        attrs = fact['attrs']
        context = parser.contexts.get(attrs.get('contextref'))
        unit = parser.units.get(attrs.get('unitref'))
        number = _number(fact)
        if not context or context['dimensioned'] or not unit or unit['divided'] or len(unit['measures']) != 1 or number is None:
            continue
        if context['entity'].strip().lstrip('0') != str(cik).lstrip('0'):
            continue
        start = context['start'].strip() or None
        end = context['end'].strip() or context['instant'].strip()
        try:
            date.fromisoformat(end)
            if start:
                date.fromisoformat(start)
            if (bool(context['end'].strip()) == bool(context['instant'].strip())
                    or bool(start) != bool(context['end'].strip())):
                continue
        except ValueError:
            continue
        measure = unit['measures'][0].strip()
        expected_units = {'iso4217:USD': 'USD', 'xbrli:shares': 'shares'}
        if measure not in expected_units or not attrs.get('name', '').startswith('us-gaap:'):
            continue
        key = (attrs['name'].split(':', 1)[1], start, end, expected_units[measure])
        candidates.setdefault(key, []).append(number)
    results = []
    for obs in observations:
        status, filing_value = 'not comparable', None
        if obs['accession'] == accession:
            matches = candidates.get((obs['tag'], obs.get('start'), obs['end'], obs['unit']), [])
            distinct = {value for value, _ in matches}
            if len(distinct) > 1:
                status = 'conflicting filing facts'
            elif matches:
                value = matches[0][0]
                filing_value = float(value)
                delta = abs(value - Decimal(str(obs['value'])))
                tolerance = min(t for _, t in matches)
                status = 'exact agreement' if not delta else 'within reported rounding' if delta <= tolerance else 'discrepancy'
        results.append({'Metric': obs['metric'], 'Period': obs['end'], 'Tag': obs['tag'],
                        'Status': status, 'Company Facts value': obs['value'],
                        'Original filing value': filing_value, 'Unit': obs['unit'],
                        'Accession': obs['accession']})
    return results


def check_original_filing(gateway, report):
    """One bounded request, only to a validated recent annual SEC document."""
    filings = [f for f in report.get('filings', []) if f['form'] in {'10-K', '10-K/A'}]
    if not filings:
        raise ValueError('No recent annual filing available')
    filing = max(filings, key=lambda f: (f['filing_date'], f['accession']))
    document = urlsplit(filing['url']).path.rsplit('/', 1)[-1]
    source = gateway.fetch('filing', report['company'].cik, accession=filing['accession'], document=document)
    research = report.get('research') or {}
    observations = [o for h in research.get('history', []) for o in h['observations'].values() if o]
    return {'rows': compare_filing(source['data'], report['company'].cik, filing['accession'], observations),
            'url': source['url'], 'retrieved_at': source['retrieved_at'], 'accession': filing['accession']}
