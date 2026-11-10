"""Chromium QA for useful volatility curves and optional 3D/heatmap views."""
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

output = Path("/tmp/qi-browser/volatility")
output.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch()
    for width in (390, 768, 1440):
        page = browser.new_page(viewport={"width": width, "height": 1000})
        page.goto("http://127.0.0.1:18526")
        heading = page.get_by_role("heading", name="Volatility Intelligence", exact=True)
        expect(heading).to_be_visible(timeout=60000)
        chart = page.locator('[data-testid="stPlotlyChart"]')
        expect(chart).to_be_visible()
        js_type = (
            "document.querySelector('[data-testid=stPlotlyChart] "
            ".js-plotly-plot')?.data?.[0]?.type"
        )
        page.wait_for_function(f"{js_type} === 'scatter'")
        headings = page.get_by_role("heading").all_text_contents()
        assert (
            headings.index("Historical price chart")
            < headings.index("Volatility Intelligence")
            < headings.index("Understanding the numbers")
        )
        chart.scroll_into_view_if_needed()
        page.screenshot(path=str(output / f"curve-{width}.png"))

        # Selecting an expiry must update the displayed values and curve.
        page.get_by_text("Time until expiration", exact=True).scroll_into_view_if_needed()
        page.get_by_label("Time until expiration").click()
        page.get_by_text("90 days", exact=True).last.click()
        page.wait_for_function(
            "document.querySelector('[data-testid=stPlotlyChart] "
            ".js-plotly-plot')?.data?.[0]?.type === 'scatter'"
        )
        page.get_by_text("3D surface", exact=True).click()
        page.wait_for_function(f"{js_type} === 'surface'")
        expect(page.get_by_role("button", name="Reset camera")).to_be_visible()
        chart.scroll_into_view_if_needed()
        page.screenshot(path=str(output / f"surface-{width}.png"))
        page.get_by_role("button", name="Reset camera").click()
        page.get_by_text("2D heatmap", exact=True).click()
        page.wait_for_function(f"{js_type} === 'heatmap'")
        chart.scroll_into_view_if_needed()
        page.screenshot(path=str(output / f"heatmap-{width}.png"))
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        expect(page.locator('[data-testid="stException"]')).to_have_count(0)
        page.close()
    browser.close()
print("Volatility curve/3D/heatmap responsive browser QA passed")
