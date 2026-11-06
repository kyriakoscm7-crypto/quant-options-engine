"""Browser checks for synthetic factor evidence, never live-data assertions."""
import argparse
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument("--channel", default="chrome")
args = parser.parse_args()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, **({'channel': args.channel} if args.channel else {}))
    page = browser.new_page(viewport={'width': 1440, 'height': 1000})
    page.goto('http://127.0.0.1:18514')
    page.get_by_role('button', name='Find research candidates', exact=True).click()
    expect(page.get_by_text('Fundamental trajectory', exact=True)).to_be_visible()
    expect(page.get_by_text('Why investigate · Quality compounders:', exact=False).first).to_be_visible()
    page.get_by_text('Stress the operating thesis · user assumptions', exact=True).click()
    expect(page.get_by_text('Hypothetical operating income', exact=True)).to_be_visible()
    before = page.get_by_test_id('stMetricValue').inner_text()
    slider = page.get_by_test_id('stSlider').filter(has_text='Revenue change (%)').get_by_role('slider')
    slider.focus()
    slider.press('End')
    expect(page.get_by_test_id('stMetricValue')).not_to_have_text(before)
    page.get_by_text('Factor contributions, formulas & filing evidence', exact=True).click()
    expect(page.get_by_text('Fixed-anchor normalization:', exact=False)).to_be_visible()
    page.get_by_text('Factor contributions, formulas & filing evidence', exact=True).click()
    out = Path('docs/images/discover-factors')
    out.mkdir(parents=True, exist_ok=True)
    for width in (390, 768, 1440):
        page.set_viewport_size({'width': width, 'height': 1000})
        page.get_by_test_id('stMain').evaluate('el => el.scrollTop = 0')
        page.screenshot(path=str(out / f'synthetic-factors-{width}.png'), full_page=True)
        page.get_by_role('heading', name='Synthetic QAALPHA · QAALPHA', exact=True).scroll_into_view_if_needed()
        page.screenshot(path=str(out / f'synthetic-trajectory-{width}.png'), full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
    page.get_by_test_id('stRadioGroup').get_by_text('QAMISSING · Synthetic QAMISSING', exact=True).click()
    expect(page.get_by_text('Compatible annual revenue and operating income required;', exact=False)).to_be_visible()
    assert not page.locator('[data-testid="stException"]').count()
    browser.close()
print('Synthetic factor browser: ranking, evidence, scenario control, missing data and 390/768/1440px passed')
