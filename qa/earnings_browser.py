"""Large synthetic week: bounded widgets, search, filtering, navigation, mobile."""
from pathlib import Path

from playwright.sync_api import sync_playwright

output = Path('/tmp/qi-browser/earnings')
output.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch()
    for width in (1440, 390):
        page = browser.new_page(viewport={'width': width, 'height': 1000})
        page.goto('http://127.0.0.1:18525')
        page.get_by_text('Showing 10', exact=False).wait_for()
        assert page.locator('.earnings-card').count() == 10
        assert page.get_by_role('button', name='Research ').count() == 10
        assert page.get_by_role('button', name='Refresh', exact=True).count() == 0
        page.screenshot(path=str(output / f'calendar-{width}.png'), full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        page.get_by_role('button', name='Show 10 more', exact=True).click()
        page.get_by_text('Showing 20', exact=False).wait_for()
        assert page.locator('.earnings-card').count() == 20
        search = page.get_by_role('textbox', name='Search earnings companies')
        search.fill('absent')
        search.press('Enter')
        page.get_by_text('0 matching earnings events', exact=False).wait_for()
        search.fill('T1269')
        search.press('Enter')
        page.get_by_role('button', name='Research T1269', exact=True).wait_for()
        assert page.locator('.earnings-card').count() == 1
        search.fill('')
        search.press('Enter')
        page.get_by_text('Showing 10', exact=False).wait_for()
        page.get_by_role('combobox', name='Reporting day').click()
        page.get_by_role('option').filter(has_text='Mon, Nov 09').click()
        page.get_by_text('254 matching earnings events', exact=False).wait_for()
        assert page.locator('.earnings-card').count() == 10
        page.get_by_role('button', name='Research T0000', exact=True).click()
        page.get_by_text('Research selection: T0000', exact=True).wait_for()
        page.close()
    browser.close()
print('Earnings desktop/mobile browser regression passed')
