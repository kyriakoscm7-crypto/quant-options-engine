"""Responsive visual QA for the new Learn home and premium masterclass."""
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

output = Path("/tmp/qi-browser/learn")
output.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    for width in (390, 768, 1440):
        page = browser.new_page(viewport={"width": width, "height": 960})
        page.goto("http://127.0.0.1:18527")
        expect(page.get_by_role("heading", name="Understand money. Think like an analyst.")).to_be_visible(timeout=60000)
        expect(page.get_by_role("heading", name="Why do option premiums change?")).to_be_visible()
        expect(page.get_by_role("button", name="Start featured options masterclass")).to_be_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.screenshot(path=str(output / f"home-{width}.png"), full_page=True)

        page.get_by_role("button", name="Start featured options masterclass").click()
        expect(page.get_by_role("heading", name="Why do option premiums change?")).to_be_visible()
        journey = page.locator(".qi-lesson-v2 .journey-map")
        expect(journey).to_be_visible()
        height = journey.bounding_box()["height"]
        assert height < (1100 if width == 390 else 620), (width, height)
        start = page.get_by_role("button", name="Start learning — Chapter 1")
        expect(start).to_be_visible()
        assert start.bounding_box()["height"] >= 60
        page.screenshot(path=str(output / f"overview-{width}.png"), full_page=True)
        start.click()
        expect(page.get_by_role("heading", name="What are you buying?")).to_be_visible()
        expect(page.get_by_role("button", name="Back to lesson overview")).to_be_visible()
        assert page.get_by_role("button", name="Previous chapter").count() == 0
        chapter_one = page.locator("main").inner_text()
        assert "$100" in chapter_one and "$10,000" in chapter_one
        assert "$350" in chapter_one and "**" not in chapter_one
        page.screenshot(path=str(output / f"chapter1-{width}.png"), full_page=True)
        page.get_by_role("button", name="Next chapter").click()
        expect(page.get_by_role("heading", name="What makes up the premium?")).to_be_visible()
        expect(page.get_by_text("$5.00 intrinsic", exact=False)).to_be_visible()
        expect(page.get_by_text("$3.00 time value", exact=False)).to_be_visible()
        chapter_two = page.locator("main").inner_text()
        assert "$100" in chapter_two and "$105" in chapter_two
        assert "$8" in chapter_two and "**" not in chapter_two
        expect(page.get_by_role("button", name="Previous chapter")).to_be_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.screenshot(path=str(output / f"chapter2-{width}.png"), full_page=True)

        page.get_by_role("button", name="Next chapter").click()
        expect(page.get_by_role("heading", name="What moves an option premium?")).to_be_visible()
        page.get_by_role("button", name="Next chapter").click()
        expect(page.get_by_role("heading", name="Experiment with option prices")).to_be_visible()
        expect(page.get_by_role("slider", name="Stock price ($)")).to_be_visible()
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        expect(page.locator('[data-testid="stException"]')).to_have_count(0)
        page.screenshot(path=str(output / f"interactive-{width}.png"), full_page=True)
        page.close()
    browser.close()
print("Learn 2.0 responsive homepage, teaching navigation and option model passed")
