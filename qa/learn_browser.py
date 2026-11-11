"""Chromium quality gate for Learn's guided beginner-to-advanced progression."""
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

output = Path("/tmp/qi-browser/learn")
output.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    for width in (390, 768, 1440):
        page = browser.new_page(viewport={"width": width, "height": 960})
        page.goto("http://127.0.0.1:18527")
        expect(page.get_by_role(
            "heading", name="Understand money. Think like an analyst."
        )).to_be_visible(timeout=60000)
        expect(page.get_by_text(
            "Start here: your first eight chapters", exact=False
        )).to_be_visible()
        expect(page.locator(".journey-map li")).to_have_count(8)
        start = page.get_by_role("button", name="Start learning from zero")
        expect(start).to_be_visible()
        assert start.bounding_box()["height"] >= 60
        assert page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth"
        )
        page.screenshot(path=str(output / f"home-{width}.png"), full_page=True)
        start.click()
        expect(page.get_by_role(
            "heading", name="Money and Investing: From Zero"
        )).to_be_visible()
        expect(page.locator(".journey-map li")).to_have_count(8)
        page.get_by_role("button", name="Start Chapter 1").click()
        expect(page.get_by_role("heading", name="Your money and your goals")).to_be_visible()
        expect(page.get_by_role("button", name="Course overview")).to_be_visible()
        assert page.get_by_role("slider").count() == 0
        assert "$1,000" in page.locator("main").inner_text()
        page.screenshot(path=str(output / f"beginner-ch1-{width}.png"), full_page=True)

        # Move to the next chapter after reading to the bottom: viewport
        # should return near the top of the new chapter without manual scrolling.
        page.get_by_role("button", name="Next chapter").click()
        expect(page.get_by_role(
            "heading", name="Saving, inflation and compounding"
        )).to_be_visible()
        page.wait_for_function(
            "() => Array.from(document.querySelectorAll("
            "'[data-testid=stAppViewContainer], [data-testid=stMain], section.main'"
            ")).every(el => el.scrollTop < 100)"
        )
        assert page.get_by_role("slider").count() == 0
        assert "$1,102.50" in page.locator("main").inner_text()
        page.screenshot(path=str(output / f"beginner-ch2-{width}.png"), full_page=True)
        assert page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth"
        )
        expect(page.locator('[data-testid="stException"]')).to_have_count(0)
        # Return home, then test advanced options has guided examples, no
        # volatility slider requiring prior options knowledge.
        page.get_by_role("button", name="Back to pathway").click()
        page.get_by_role("button", name="All learning paths").click()
        page.get_by_role("button", name="Open advanced options course").click()
        expect(page.get_by_role(
            "heading", name="Why do option premiums change?"
        )).to_be_visible()
        page.get_by_role("button", name="Start learning — Chapter 1").click()
        for _ in range(3):
            page.get_by_role("button", name="Next chapter").click()
        expect(page.get_by_role(
            "heading", name="See the forces change an option price"
        )).to_be_visible()
        assert page.get_by_role("slider").count() == 0
        assert page.get_by_role("radio").count() == 0
        expect(page.get_by_text("The stock rises", exact=False)).to_be_visible()
        page.screenshot(path=str(output / f"guided-options-{width}.png"), full_page=True)
        expect(page.locator('[data-testid="stException"]')).to_have_count(0)
        page.close()
    browser.close()
print("Learn foundations, chapter scroll reset and guided options QA passed")
