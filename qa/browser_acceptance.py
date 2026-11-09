"""Real browser QA. Use fictional test notes only."""

import argparse
import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def run(base, output, channel):
    output.mkdir(parents=True, exist_ok=True)
    results = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True, **({"channel": channel} if channel else {})
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 1000}, accept_downloads=True
        )
        page = context.new_page()

        def button(name):
            return page.get_by_role("button", name=name, exact=True)

        def field(name):
            return page.get_by_role("textbox", name=name, exact=True)

        page.goto(base)
        expect(button("Open Discovery")).to_be_visible(timeout=30000)
        button("Open Discovery").click()
        page.get_by_text("Your research notebook · thesis, counterevidence & exports", exact=True).click()
        button("Add selected listing to shortlist").click()
        field("Research question").fill("QA public-company research — α")
        trigger = "FINAL FIELD — review next public filing ✓"
        field("Next review trigger").fill(trigger)
        # No blur/Enter between typing in final field and submitting.
        button("Save & prepare export").click()
        expect(
            page.get_by_text(
                "Saved revision 1. Your export includes all fields submitted above.",
                exact=True,
            )
        ).to_be_visible()
        with page.expect_download() as download:
            button("Download saved revision 1 JSON").click()
        target = output / "last-field-export.json"
        download.value.save_as(target)
        data = json.loads(target.read_text())
        assert (
            data["revision"] == 1
            and data["records"][0]["Next review trigger"] == trigger
        )
        results["late_field_download"] = {
            "bytes": target.stat().st_size,
            "revision": 1,
            "last_field_matches": True,
        }
        button("Investigate shortlisted company").click()
        # Both routes render the same notebook fields. Waiting for a field's
        # existing value can succeed on Discovery before navigation completes,
        # so typing there can be discarded by the incoming Explorer rerender.
        expect(
            page.get_by_role("heading", name="Company overview", exact=True)
        ).to_be_visible()
        expect(field("Next review trigger")).to_have_value(trigger)
        field("Thesis & valuation").fill("QA thesis from Explorer")
        button("Save & prepare export").click()
        expect(
            page.get_by_text(
                "Saved revision 2. Your export includes all fields submitted above.",
                exact=True,
            )
        ).to_be_visible()
        with page.expect_download() as download:
            button("Download saved revision 2 JSON").click()
        download.value.save_as(output / "explorer-export.json")
        assert (
            json.loads((output / "explorer-export.json").read_text())["records"][0][
                "Thesis & valuation"
            ]
            == "QA thesis from Explorer"
        )
        results["shared_notebook"] = True
        button("Model manual assumptions in Options Lab").click()
        spot = page.get_by_role("spinbutton", name="Underlying price ($)", exact=True)
        spot.fill("123")
        spot.press("Enter")
        button("Investigate these assumptions in Greeks").click()
        expect(spot).to_have_value("123.00")
        button("Dashboard").click()
        button("Open Options Lab").click()
        expect(spot).to_have_value("123.00")
        button("Stress these assumptions in Scenario Explorer").click()
        assert float(spot.input_value()) == 123
        results["model_navigation"] = True
        button("Dashboard").click()
        button("Open Stock Explorer").click()
        page.get_by_text(
            "Allow automatic TradingView panels this session", exact=True
        ).click()
        # The base branch deliberately replaced the view selector with an open
        # layout. All six official panels require the shared explicit consent.
        expect(page.locator('iframe[data-testid="stIFrame"]')).to_have_count(6)
        for heading in ["Company overview", "Historical price chart", "Financial performance",
                        "Inside the business", "Technical analysis"]:
            expect(page.get_by_role("heading", name=heading, exact=True)).to_be_visible()
        expect(field("Next review trigger")).to_have_value(trigger)
        results["consented_panels"] = {"mounted_widgets": 6, "shared_notes_preserved": True}
        for width in [390, 400, 768, 1440]:
            responsive_context = browser.new_context(
                viewport={"width": width, "height": 1000}
            )
            responsive = responsive_context.new_page()
            responsive.goto(base + "/?qi_go=research")
            expect(responsive.get_by_role("heading", name="Company overview", exact=True)).to_be_visible(timeout=30000)
            # The autocomplete component has its own iframe; only external
            # chart panels are governed by TradingView consent.
            expect(responsive.locator('iframe[data-testid="stIFrame"]')).to_have_count(0)
            # A fresh session defaults to SPY and has no shortlisted record.
            # Existing-company editing is verified in the shared notebook flow above.
            expect(responsive.get_by_text("Selected listing · AMEX:SPY", exact=True)).to_be_visible()
            expect(
                responsive.get_by_role("textbox", name="Research question", exact=True)
            ).to_have_count(0)
            expect(responsive.get_by_role("button", name="Model manual assumptions in Options Lab", exact=True)).to_be_visible()
            expect(responsive.locator('[data-testid="stException"]')).to_have_count(0)
            responsive.wait_for_timeout(500)
            responsive.screenshot(
                path=str(output / f"research-{width}.png"), full_page=True
            )
            dimensions = responsive.evaluate(
                "({width:innerWidth,scroll:document.documentElement.scrollWidth})"
            )
            assert dimensions["scroll"] <= width + 1, dimensions
            responsive_context.close()
        results["responsive_widths"] = [390, 400, 768, 1440]
        other_context = browser.new_context()
        other = other_context.new_page()
        other.goto(base)
        other.get_by_role("button", name="Open Discovery", exact=True).click()
        other.get_by_text("Your research notebook · thesis, counterevidence & exports", exact=True).click()
        expect(
            other.get_by_text(
                "Select a company to begin a source-linked research record.", exact=True
            )
        ).to_be_visible()
        results["independent_session_empty"] = True
        other_context.close()
        context.close()
        browser.close()
    (output / "browser-results.json").write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:18501")
    parser.add_argument(
        "--output", type=Path, default=Path("/private/tmp/qi-fixes-browser")
    )
    parser.add_argument("--channel", default="chrome")
    args = parser.parse_args()
    run(args.base, args.output, args.channel)
