"""Browser acceptance for the isolated offline news preview on port 18502."""
import argparse
import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def run(base, output, channel):
    output.mkdir(parents=True, exist_ok=True)
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, **({'channel': channel} if channel else {}))
        for width in (390, 1440):
            for scenario in ('Available', 'Stale', 'Unavailable', 'Empty', 'Disabled'):
                context = browser.new_context(viewport={'width': width, 'height': 1000})
                context.route('https://**/*', lambda route: route.abort())
                page = context.new_page()
                page.goto(base)
                control = page.get_by_role('combobox', name='QA source scenario', exact=True)
                expect(control).to_be_visible(timeout=30000)
                if scenario != 'Available':
                    control.click()
                    page.get_by_role('option', name=scenario, exact=True).click()
                page.get_by_text('Connect official SEC directory and configured news sources', exact=True).click()
                page.get_by_role('textbox', name='Company name or SEC ticker', exact=True).fill('AAPL')
                page.get_by_role('textbox', name='Company name or SEC ticker', exact=True).press('Enter')
                page.get_by_role('button', name='Build intelligence report', exact=True).click()
                expect(page.get_by_text('CIK 0000320193', exact=False)).to_be_visible(timeout=30000)
                expect(page.locator('[data-testid="stException"]')).to_have_count(0)
                if scenario in ('Available', 'Stale'):
                    expect(page.get_by_text('First seen (publication time unknown)', exact=False)).to_be_visible()
                if scenario in ('Stale', 'Unavailable'):
                    expect(page.get_by_text(f'SEC: {scenario.lower()}', exact=False)).to_be_visible()
                if scenario == 'Disabled':
                    expect(page.get_by_text('QA fixture: disabled', exact=True)).to_be_visible()
                page.get_by_text('CIK 0000320193', exact=False).scroll_into_view_if_needed()
                page.get_by_role('tab', name='Headlines', exact=True).scroll_into_view_if_needed()
                page.screenshot(path=str(output / f'news-{scenario.lower()}-{width}.png'), full_page=True)
                dimensions = page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')
                assert dimensions['scroll'] <= width + 1, dimensions
                page.get_by_role('tab', name='Official filings', exact=True).click()
                if scenario == 'Available':
                    expect(page.get_by_role('link', name='Open SEC filing ↗', exact=True)).to_have_attribute('href', 'https://www.sec.gov/Archives/edgar/data/320193/000032019326000001/qa.htm')
                page.get_by_role('tab', name='Coverage & sources', exact=True).click()
                expect(page.locator('[data-testid="stDataFrame"]')).to_be_visible()
                query = page.get_by_role('textbox', name='Company name or SEC ticker', exact=True)
                query.fill('MSFT')
                query.press('Enter')
                expect(page.get_by_text('CIK 0000320193', exact=False)).to_have_count(0)
                results.append({'width': width, 'scenario': scenario, 'no_overflow': True,
                                'changed_company_invalidates_report': True})
                context.close()
        browser.close()
    (output / 'news-browser-results.json').write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='http://127.0.0.1:18502')
    parser.add_argument('--output', type=Path, default=Path('/private/tmp/qi-release-news-browser'))
    parser.add_argument('--channel', default='chrome')
    args = parser.parse_args()
    run(args.base, args.output, args.channel)
