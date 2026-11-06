# Proposed PR #12 update

Suggested title: Discover: in-app fundamental screening and company investigations

Discover previously made users find companies in an external screener and then manually request individual evidence briefs. The new flow screens a bounded company universe inside the app, explains every criterion, and opens a selected company's financial evidence and research risks. Stock Explorer and the session notebook retain their existing behavior.

## Behavior

- Choose either of two editorial six-company starting sets or enter up to eight exact SEC tickers. These are not index constituents, market-wide coverage or recommendations. Fetches are user-initiated and retain the existing SEC cache, identity checks, shared request budget and cooldown.
- Compare four disclosed annual criteria: net margin at least 10%; operating cash/revenue at least 10%; liabilities/assets between zero and 60%; current ratio at least 1. Order eligible companies by count met, then ticker. Equal weights and thresholds are research heuristics, not calibrated investment scores or expected returns.
- Require all four comparable ratios, no excluded conflicting facts and an annual period within 550 days. Missing or stale evidence remains inspectable but unranked. Filtering never turns missing data into zero. Failed refreshes clear prior results rather than substituting facts.
- Research cards show annual revenue, income, operating cash, ratios, screening reasons, issuer/CIK, source and filing dates, missing/revised/conflicting data, accounting risk prompts and recent filings. Multi-company comparison remains available in an expander.
- Valuation is explicitly unavailable without an admitted, dated market-price/share-count integration. No fair values, prices, market caps or P/E multiples are synthesized from SEC facts.
- Earnings/catalysts display only confirmed evidence admitted through the existing licensed-source boundary. No providers are currently admitted. Analyst coverage remains unavailable. Filing dates and estimated earnings dates do not become catalysts.
- Discover no longer embeds TradingView. Stock Explorer's consent controls and browser panels are unchanged. The compatibility Scanner renderer retains an optional collapsed screener; normal Scanner navigation continues to Discover.

## Components

`app/intelligence/discover_screen.py`, `dashboard/discover_intelligence.py`, `dashboard/market_research_workspace.py`, regression tests, and isolated `qa/discover_preview.py` / `qa/discover_browser.py`. The CI browser job now includes the isolated fixture flow. QA fixtures are labelled, fictional and never imported by production navigation.

## Limitations

Live SEC calls were not exercised: an operator must configure a genuine `QI_SEC_USER_AGENT` contact before activation. No invented contact is used. Coverage remains annual USD US-GAAP SEC evidence; no quarterly/TTM, sector adjustment, comprehensive business-risk extraction, market-wide universe, valuation feed, live analyst feed or earnings adapter is claimed. Reporting dates can differ and filings are issuer-reported evidence, not independent corroboration. Separate machines still require an operator-managed shared SEC request budget.

## Review status

The replacement was recovered as uncommitted work above `00f1ea82ca571521e9372786090443f3351107c7` on `feature/discover-intelligence-v2`. PR #12 was verified open with that same remote head before preparing this commit. This change is intended for the existing feature PR only; no merge or deployment is authorized.

## Local validation

- Full suite: **2,125 passed**, 208 existing warnings. Final run: 26.25 seconds. Added seven screening/UI regression cases.
- Ruff over app/tests/dashboard/qa: passed. Bandit medium/high check over app/dashboard: passed. Dependency compatibility and whitespace checks: passed.
- Chrome against the full application: notebook last-field export and revisions, shared notebook navigation, model handoffs, six consented Stock Explorer panels, 390/400/768/1440px layouts and independent session isolation passed.
- Chrome against the isolated synthetic preview: ranking/filter, candidate selection, missing evidence excluded from ranking, provider failure clearing results, no external embeds and 390/768/1440px layout checks passed. Fixture screenshots were visually inspected at desktop and mobile sizes. They are not evidence of live issuer facts or provider availability.
- Browser fixture checks are added to CI, but remote CI has not run for these local changes. No Docker build, deployment or live-provider test is claimed for this revision.

Review evidence: `docs/discover-rebuild-validation/`. Synthetic screenshots: `docs/images/discover-rebuild/`.

## Recovery verification (November 5, 2026, Toronto time)

Re-ran the 2,125-test suite successfully (208 warnings), Ruff, dependency compatibility, whitespace checks and Bandit's medium/high gate. Re-ran both browser acceptance scripts: native fixture ranking/filtering, missing evidence and failed-refresh handling, no Discover embeds, responsive layouts, six consented Stock Explorer panels, notebook exports, shared navigation and independent sessions passed. Visually inspected the native desktop candidate capture. Live SEC requests were not exercised.

Added two production-entry regression cases: both Discover and legacy Scanner navigation must render native screening, annual revenue and a candidate card without external panels. Final full suite: **2,127 passed**, 208 warnings, 26.86 seconds. Corrected the dashboard's obsolete description of Discover as an external display. Stock Explorer implementation remains unchanged.

## Get the update on another Mac checkout

Stop that checkout's running Streamlit process with Ctrl+C. In its repository directory, run `git status --short` first. If it lists local work, preserve that work before switching branches or pulling; do not reset it.

```sh
git fetch origin
git switch feature/discover-intelligence-v2
git pull --ff-only origin feature/discover-intelligence-v2
git log -1 --format='%H %s'
source .venv/bin/activate
```

Set a genuine operator contact for SEC research in the same terminal before launching (replace the placeholder with your real contact):

```sh
export QI_SEC_USER_AGENT='Quant Intelligence your-real-contact@your-domain'
python -m streamlit run dashboard/main.py
```

Open the local URL printed by Streamlit, refresh the browser and select Discover → Scan & investigate. Expect “Find your next research question”, a research universe selector and “Find research candidates”. Click that button to fetch evidence and show candidates. Without the contact setting, Discover explains that company briefs are not connected; it still must not show the oversized TradingView screener. SEC/provider errors are shown rather than replaced with example data. Hosted production remains unchanged by this feature-branch update.
