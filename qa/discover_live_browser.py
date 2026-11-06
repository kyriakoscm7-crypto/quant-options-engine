"""Opt-in browser smoke check against a running app with genuine SEC access."""

import argparse
import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--base", default="http://127.0.0.1:18501")
parser.add_argument("--output", type=Path, default=Path("/tmp/qi-discover-live"))
args = parser.parse_args()
out = args.output
out.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    page = b.new_page(viewport={"width": 1440, "height": 1000})
    page.goto(args.base)
    page.get_by_role("button", name="Open Discovery", exact=True).click()
    field = page.get_by_role("textbox", name="Companies to investigate", exact=True)
    field.fill("AAPL, MSFT")
    page.get_by_role("button", name="Find research candidates", exact=True).click()
    expect(
        page.get_by_role("radio", name="AAPL · Apple Inc.", exact=True)
    ).to_be_visible(timeout=90000)
    expect(
        page.get_by_role("radio", name="MSFT · MICROSOFT CORP", exact=True)
    ).to_be_visible()
    assert not page.get_by_test_id("stException").count()
    expect(page.get_by_text("Evidence retrieved", exact=False)).to_be_visible()
    page.get_by_role("heading", name="Research candidates", exact=True).evaluate(
        "el => el.scrollIntoView({block: 'start'})"
    )
    page.wait_for_timeout(700)
    page.screenshot(path=str(out / "live-desktop.png"), full_page=True)
    for width in [390, 768]:
        page.set_viewport_size({"width": width, "height": 1000})
        page.wait_for_timeout(1000)
        close = page.get_by_role("button", name="Collapse sidebar", exact=True)
        if close.is_visible():
            close.click()
        page.wait_for_timeout(500)
        assert page.evaluate("document.documentElement.scrollWidth") <= width + 1
        page.get_by_role("heading", name="Research candidates", exact=True).evaluate(
            "el => el.scrollIntoView({block: 'start'})"
        )
        page.wait_for_timeout(700)
        page.screenshot(path=str(out / f"live-{width}.png"), full_page=True)
    (out / "results.json").write_text(
        json.dumps(
            {
                "live_SEC": True,
                "tickers": ["AAPL", "MSFT"],
                "cards_and_detail": True,
                "responsive_widths": [390, 768, 1440],
            },
            indent=2,
        )
    )
    b.close()
print("Live SEC cards and provenance browser check passed")
