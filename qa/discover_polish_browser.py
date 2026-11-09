"""Real-browser UI acceptance using explicitly synthetic offline fixtures."""
import argparse
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect, sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--base', default='http://127.0.0.1:18532')
parser.add_argument('--channel', default='chrome')
parser.add_argument('--output', type=Path, default=Path('docs/images/discover-polish'))
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, **({'channel': args.channel} if args.channel else {}))
    page = browser.new_page(viewport={'width': 1440, 'height': 1100})
    page.goto(args.base)
    page.get_by_role('button', name='Find research candidates', exact=True).click()
    open_alpha = page.get_by_role('button', name='Open QAALPHA research →', exact=True)
    expect(open_alpha).to_be_visible()
    expect(page.get_by_role('img', name='Operating margin · observed annual periods; gaps are missing').first).to_be_visible()
    for width in (1440, 768, 390):
        page.set_viewport_size({'width': width, 'height': 1100})
        open_alpha.evaluate("el => el.scrollIntoView({block:'center'})")
        page.wait_for_timeout(400)
        page.screenshot(path=str(args.output / f'synthetic-cards-{width}.png'), full_page=False)
        boxes = [page.get_by_role('button', name=f'Open {t} research →', exact=True).bounding_box() for t in ('QAALPHA', 'QABETA')]
        assert (abs(boxes[0]['y'] - boxes[1]['y']) < 5) if width > 700 else (boxes[1]['y'] > boxes[0]['y'] + 100)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
    page.set_viewport_size({'width': 1440, 'height': 1100})
    page.get_by_text('Research options & comparison', exact=True).click()
    search = page.get_by_role('textbox', name='Search candidates', exact=True)
    search.fill('qamissing')
    search.press('Enter')
    expect(open_alpha).to_have_count(0)
    expect(page.get_by_text('Why unranked', exact=False)).to_be_visible()
    search.fill('')
    search.press('Enter')
    expect(open_alpha).to_be_visible()
    # Cards can become visible before the rerun has finished reconciling the
    # comparison widget. Opening it mid-rerun can close its option list.
    expect(page.get_by_test_id('stStatusWidget')).to_be_hidden()
    comparison_widget = page.get_by_test_id('stMultiSelect')
    compare = comparison_widget.get_by_role('combobox')
    for ticker in ('QAALPHA', 'QABETA'):
        try:
            option = page.get_by_role('option', name=f'{ticker} · Synthetic {ticker}', exact=True)
            # A pending Streamlit rerender can close an otherwise valid picker.
            # Reopen only a closed menu; never retry a selection or overlook a
            # missing option in an open list. Exact selected-chip and server-side
            # comparison assertions below still have to pass.
            for attempt in range(3):
                if compare.get_attribute('aria-expanded') != 'true':
                    comparison_widget.get_by_role('button', name='Open', exact=True).click()
                try:
                    expect(option).to_be_visible(timeout=2000)
                    break
                except AssertionError:
                    if compare.get_attribute('aria-expanded') == 'true' or attempt == 2:
                        raise
            option.click()
        except (PlaywrightTimeoutError, AssertionError):
            page.screenshot(path=str(args.output / 'comparison-failure.png'), full_page=True)
            print({'comparison_input': compare.input_value(),
                   'expanded': compare.get_attribute('aria-expanded'),
                   'visible_options': page.get_by_role('option').all_text_contents(),
                   'widget': page.get_by_test_id('stMultiSelect').inner_text()}, flush=True)
            raise
        expect(comparison_widget.get_by_text(f'{ticker} · Synthetic {ticker}', exact=True)).to_be_visible()
        expect(page.get_by_test_id('stStatusWidget')).to_be_hidden()
    expect(page.get_by_text('Your comparison', exact=True)).to_be_visible()
    page.get_by_text('Your comparison', exact=True).click()
    open_alpha.click()
    expect(page.get_by_role('heading', name='Synthetic QAALPHA · QAALPHA', exact=True)).to_be_visible()
    page.get_by_text('Try a business scenario', exact=True).click()
    expect(page.get_by_text('Test your operating assumptions', exact=True)).to_be_visible()
    before = page.get_by_test_id('stMetricValue').inner_text()
    slider = page.get_by_test_id('stSlider').filter(has_text='Revenue change (%)').get_by_role('slider')
    slider.focus()
    slider.press('End')
    expect(page.get_by_test_id('stMetricValue')).not_to_have_text(before)
    page.get_by_text('How the pattern is calculated', exact=True).click()
    expect(page.get_by_text('Fixed-anchor normalization:', exact=False)).to_be_visible()
    page.get_by_text('Sources & evidence checks', exact=True).click()
    expect(page.get_by_text('Independent financial-source corroboration has not run.', exact=False)).to_be_visible()
    expect(page.get_by_text('Remaining-factor means:', exact=False)).to_be_visible()
    page.get_by_role('button', name='Check original annual filing', exact=True).click()
    expect(page.get_by_text('Original filing check unavailable.', exact=False)).to_be_visible()
    for width in (1440, 390):
        page.set_viewport_size({'width': width, 'height': 1100})
        page.get_by_role('heading', name='Synthetic QAALPHA · QAALPHA', exact=True).evaluate("el => el.scrollIntoView({block:'start'})")
        page.wait_for_timeout(400)
        page.screenshot(path=str(args.output / f'synthetic-detail-{width}.png'), full_page=False)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
    page.get_by_role('button', name='← Back to candidates', exact=True).click()
    expect(page.get_by_role('heading', name='Synthetic QAALPHA · QAALPHA', exact=True)).to_have_count(0)
    assert not page.get_by_test_id('stException').count()
    browser.close()
print('Browser passed: grid geometry, responsive overflow, search, drilldown/back, keyboard scenario, factor evidence.')
