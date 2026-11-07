"""Real Chromium regression against the synthetic earnings preview."""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto('http://127.0.0.1:18525')
    page.get_by_text('Synthetic Company (TEST)', exact=False).wait_for()
    assert page.get_by_role('radio').count() == 0
    assert page.get_by_role('combobox').count() == 0
    assert page.get_by_role('button', name='Refresh', exact=True).count() == 0
    page.get_by_role('textbox', name='Search earnings companies').fill('absent')
    page.get_by_role('textbox', name='Search earnings companies').press('Enter')
    page.get_by_text('0 matching earnings events', exact=False).wait_for()
    page.get_by_role('textbox', name='Search earnings companies').fill('TEST')
    page.get_by_role('textbox', name='Search earnings companies').press('Enter')
    page.get_by_role('button', name='Research', exact=True).click()
    page.get_by_text('Research selection: TEST', exact=True).wait_for()
    browser.close()
print('Earnings browser regression passed')
