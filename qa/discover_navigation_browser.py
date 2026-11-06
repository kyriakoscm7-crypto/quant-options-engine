"""Production routing, responsive sidebar, empty calendar and keyboard checks."""
import argparse
import re
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--base', default='http://127.0.0.1:18535')
parser.add_argument('--channel', default='chrome')
parser.add_argument('--output', type=Path, default=Path('docs/images/discover-simple'))
args = parser.parse_args()
output = args.output
output.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, **({'channel': args.channel} if args.channel else {}))
    page = browser.new_page(viewport={'width': 1440, 'height': 1100})
    page.goto(args.base + '/?qi_go=discover')
    sidebar = page.get_by_test_id('stSidebar')
    find = sidebar.get_by_role('button', name=re.compile('Find stocks$'))
    earnings = sidebar.get_by_role('button', name=re.compile('Earnings this week$'))
    expect(find).to_be_visible()
    expect(earnings).to_be_visible()
    assert not page.get_by_role('tab', name=re.compile('Find stocks|Earnings this week')).count()
    expect(page.get_by_role('heading', name='Find stocks', exact=True)).to_be_visible()
    earnings.focus()
    earnings.press('Enter')
    expect(page.get_by_role('heading', name='Earnings this week', exact=True)).to_be_visible()
    expect(page.get_by_text('Earnings dates are unavailable.', exact=False)).to_be_visible()
    heading = page.get_by_role('heading', level=3).first
    initial = heading.inner_text()
    page.get_by_role('button', name='Next week →', exact=True).click()
    expect(heading).not_to_have_text(initial)
    page.get_by_role('button', name='This week', exact=True).click()
    expect(heading).to_have_text(initial)
    for width in (1440, 768, 390):
        page.set_viewport_size({'width': width, 'height': 1100})
        page.wait_for_timeout(350)
        page.screenshot(path=str(output / f'calendar-{width}.png'), full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
        if earnings.bounding_box()['x'] < 0:
            page.get_by_role('button', name='Expand sidebar').click()
        expect(earnings).to_be_in_viewport()
        page.wait_for_timeout(400)
        expect(find).to_be_visible()
        earnings.focus()
        assert earnings.evaluate('el => el === document.activeElement')
        page.screenshot(path=str(output / f'sidebar-{width}.png'))
    find.focus()
    find.press('Enter')
    page.set_viewport_size({'width': 1440, 'height': 1100})
    expect(page.get_by_role('heading', name='Find stocks', exact=True)).to_be_visible()
    expect(page.get_by_text('Your research notebook · thesis, counterevidence & exports', exact=True)).to_be_attached()
    sidebar.get_by_role('button', name=re.compile('Research$')).click()
    sidebar.get_by_role('button', name=re.compile('Stock Explorer$')).click()
    expect(page.get_by_role('heading', name=re.compile('Stock Explorer'))).to_be_visible()
    assert not page.get_by_test_id('stException').count()
    browser.close()
print('Passed: two sidebar routes, keyboard activation/focus, weekly navigation, source empty state, notebook and Stock Explorer, overflow at 390/768/1440.')
