"""Chromium checks for a shareable, clearly simulated volatility explorer."""
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

output = Path("/tmp/qi-browser/volatility")
output.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch()
    for width in (390, 768, 1440):
        page = browser.new_page(viewport={"width": width, "height": 1000})
        page.goto("http://127.0.0.1:18526")
        heading = page.get_by_role("heading", name="Volatility Lab", exact=True)
        expect(heading).to_be_visible(timeout=60000)
        expect(page.get_by_text("What does volatility actually mean?", exact=True)).to_be_visible()
        expect(page.get_by_text("Illustrative only.", exact=False)).to_be_visible()
        chart = page.locator('[data-testid="stPlotlyChart"]').first
        expect(chart).to_be_visible()
        page.wait_for_function(
            "document.querySelector('[data-testid=stPlotlyChart] "
            ".js-plotly-plot')?.data?.[0]?.type === 'scatter'"
        )
        expect(page.locator('[data-testid="stMetric"]')).to_have_count(0)
        chart.scroll_into_view_if_needed()
        page.screenshot(path=str(output / f"public-scenario-{width}.png"))
        page.get_by_text("Lower uncertainty", exact=True).click()
        expect(page.get_by_role("radio", name="Lower uncertainty")).to_be_checked()
        expect(chart).to_be_visible()
        page.get_by_text(
            "Advanced: explore the 3D educational volatility lab", exact=True
        ).click()
        page.get_by_text("Open advanced simulation", exact=True).click()
        page.get_by_text("3D surface", exact=True).click()
        page.wait_for_function(
            "Array.from(document.querySelectorAll('[data-testid=stPlotlyChart] "
            ".js-plotly-plot')).some(el => el.data?.[0]?.type === 'surface')"
        )
        page.get_by_role("button", name="Reset camera").click()
        page.get_by_text("2D heatmap", exact=True).click()
        page.wait_for_function(
            "Array.from(document.querySelectorAll('[data-testid=stPlotlyChart] "
            ".js-plotly-plot')).some(el => el.data?.[0]?.type === 'heatmap')"
        )
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        expect(page.locator('[data-testid="stException"]')).to_have_count(0)
        page.close()
    browser.close()
print("Public scenario and optional advanced simulation browser QA passed")
