"""Browser acceptance of isolated, prominently labelled synthetic QA evidence."""
import argparse
import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def run(base, output, channel):
    output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, **({"channel": channel} if channel else {}))
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.goto(base)
        expect(page.get_by_text("SYNTHETIC QA FIXTURES", exact=False)).to_be_visible()
        page.get_by_role("button", name="Find research candidates", exact=True).click()
        expect(page.get_by_text("4 of 4 criteria met", exact=True).first).to_be_visible()
        page.get_by_role("button", name="Open QAALPHA research →", exact=True).click()
        page.get_by_text("Event coverage & next investigation", exact=True).click()
        expect(page.get_by_text("No confirmed licensed catalyst available.", exact=False)).to_be_visible()
        assert page.locator('iframe[data-testid="stIFrame"]').count() == 0
        page.get_by_role("button", name="← Back to candidates", exact=True).click()
        page.get_by_role("button", name="Open QAMISSING research →", exact=True).click()
        expect(page.get_by_test_id("stMarkdownContainer").get_by_text("Not ranked: missing, conflicting or older than 550 days annual evidence", exact=True).last).to_be_visible()
        page.get_by_role("button", name="← Back to candidates", exact=True).click()
        page.get_by_text("Research options & comparison", exact=True).click()
        page.get_by_text("Show only candidates meeting at least three criteria", exact=True).click()
        expect(page.get_by_text("4 of 4 criteria met", exact=True).first).to_be_visible()
        page.get_by_role("button", name="Open QAALPHA research →", exact=True).click()
        for width in (390, 768, 1440):
            page.set_viewport_size({"width": width, "height": 1000})
            page.get_by_role("heading", name="Synthetic QAALPHA · QAALPHA", exact=True).scroll_into_view_if_needed()
            page.screenshot(path=str(output / f"synthetic-discover-{width}.png"), full_page=True)
            dimensions = page.evaluate("({width: innerWidth, scroll: document.documentElement.scrollWidth})")
            assert dimensions["scroll"] <= width + 1
        page.get_by_text("Research universe & SEC search", exact=True).click()
        field = page.get_by_role("textbox", name="Companies to investigate", exact=True)
        field.fill("QAERROR")
        page.get_by_role("button", name="Find research candidates", exact=True).click()
        expect(page.get_by_text("QAERROR: SEC evidence unavailable", exact=False)).to_be_visible()
        expect(page.get_by_text("4 of 4 criteria met", exact=True)).to_have_count(0)
        browser.close()
    result = {"synthetic_fixture_only": True, "ranking_and_filter": True,
              "missing_unranked": True, "provider_failure_clears_results": True,
              "no_external_panel": True, "responsive_widths": [390, 768, 1440]}
    (output / "results.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:18512")
    parser.add_argument("--output", type=Path, default=Path("/tmp/qi-discover-cards"))
    parser.add_argument("--channel", default="chrome")
    args = parser.parse_args()
    run(args.base, args.output, args.channel)
