# Discover UI polish

The Discover presentation now uses a two-column desktop grid and a single-column mobile layout. Cards show issuer identity, explicitly labeled accounting archetype fit, four reported factors, an observed annual operating-margin sparkline, concise factor strengths, annual period and SEC retrieval timestamp. Missing factors and source timestamps remain unavailable; the sparkline breaks at missing observations and is not a forecast.

Search matches company names and tickers without another provider request. Users can choose an archetype, hide unranked candidates, sort by fit/name/revenue CAGR/operating margin, and select up to four companies for comparison. Missing sort values remain last; ties use ticker. Comparison survives search and removes selections no longer present after refresh. Annual periods and display units remain visible.

Opening research replaces the grid with a focused company workspace; Back restores the candidate controls. The workspace includes the selected pattern, margin history, expandable revenue/cash-flow and asset/liability charts, all eight factors and their fixed anchors, selected-pattern membership, observed downside flags, compatible-baseline operating stress controls, and SEC filing/accession/date provenance. Secondary event coverage and investigation prompts are collapsed. Setup collapses after a successful scan. Universe-specific input state prevents stale ticker defaults when changing universes.

## Verification

- Full Python test suite: 2,157 tests passed on the final implementation; existing dependency warnings remain.
- Discover/factor interaction suite: 77 tests passed, including search, empty results, comparison persistence/pruning, drilldown/back, refresh failure, missing evidence, scenario interaction, display units and both main-app Discover routes.
- Real Chrome: `qa/discover_polish_browser.py` against `QI_QA_FACTORS=1` preview, with grid geometry and overflow checks at 390/768/1440 px, company search, compare selection, drilldown/back, keyboard scenario change and factor evidence expansion.
- Legacy evidence Chrome: `qa/discover_browser.py` against the non-factor preview; ranking/filter, missing evidence, failed refresh, responsive widths and no external research iframe.
- Ruff project gate, dependency compatibility (`pip check`) and whitespace checks passed.
- Desktop/mobile screenshots in `docs/images/discover-polish/` were visually inspected. These are explicitly synthetic offline fixtures, not real issuer data or a live SEC verification. Preview is isolated from production routing.
- Explicit card text contrast against #121D35: pink #FF78B7 6.88:1, secondary #BBC7DE 9.85:1, primary #F4F6FF 15.54:1. Native Streamlit controls retain accessible labels and keyboard behavior; custom sparkline has an accessible title and a textual date/value summary. Focus has a visible pink outline.

## Scope and limits

No changes to the factor engine, formulas, anchors, scoring, source gateway, SEC admission, sector exclusions, legal or privacy rules. No investment recommendations or fabricated production facts. Fresh live SEC retrieval was not repeated for this UI revision. Native data tables scroll horizontally on small screens; browser checks ensure no document-wide overflow. No screen-reader certification or exhaustive device/browser coverage is claimed. CI must still finish on the pushed commit. No merge or deployment.
