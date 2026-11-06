# Discover — Mac setup and verified scope

## Update an existing checkout

Stop Streamlit with Ctrl+C. In your own quant-options-engine repository folder:

```sh
git status --short
```

Preserve any local work before switching or pulling. Do not reset it.

```sh
git fetch origin
git switch feature/discover-intelligence-v2
git pull --ff-only origin feature/discover-intelligence-v2
```

Use Python 3.11 (the tested version is 3.11.17). If needed, install Python with `brew install python@3.11`, then create the environment:

```sh
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
```

## Configure genuine SEC access

In the same terminal, enter your real operator email at the prompt. It is used in SEC request headers. Do not commit it to configuration files. No SEC API key is needed. The app reads the process environment; it does not automatically load `.env` files.

```sh
read "qi_contact?Your genuine SEC operator contact email: "
export QI_SEC_USER_AGENT="Quant Intelligence $qi_contact"
unset qi_contact
python scripts/check_discover_sec.py AAPL
python -m streamlit run dashboard/main.py
```

The `read` command above uses the default Mac zsh shell. Open the local URL printed by Streamlit (normally http://localhost:8501), select Discover → Scan & investigate, enter exact SEC tickers, and click **Find research candidates**. Use **Find SEC tickers by company name** for the official directory lookup. The notebook is collapsed below research. Each new terminal requires the export again; restart an already-running Streamlit process after changing the environment.

The check prints normalized SEC observations, period, filing accession, retrieval timestamps and source URLs. It does not print your contact. Exit 1 means configuration/network/identity blocked retrieval; exit 2 means no usable annual observations were retrieved. Neither means success. Missing/invalid contact sends no SEC requests. After SEC 403/429 responses, wait at least ten minutes (or longer Retry-After); do not clear the shared budget to evade cooldown.

## What works

- Explicit, bounded scans of up to eight exact SEC tickers; two editorial starting sets and arbitrary supported SEC companies via directory search. This is not a market-wide discovery feed.
- Actual SEC directory → verified CIK → submissions → XBRL companyfacts. Annual USD US-GAAP revenue, income, operating cash, assets/liabilities and current assets/liabilities retain reporting dates, filing dates, accession and source links.
- Compact company evidence cards, company comparison, selected-company financial details, accounting flags, recent filings and investigation prompts. Ratios require compatible filing contexts.
- Four disclosed screening rules: net margin ≥10%, operating cash/revenue ≥10%, liabilities/assets 0–60%, current ratio ≥1. Complete nonconflicting evidence within 550 days is required for ordering by count met, then ticker. Missing/stale/conflicting evidence remains inspectable and unranked; no return scores or recommendations.
- User-initiated retrieval, one-hour company cache, 24-hour directory cache, original retrieval timestamps, bounded payloads, no redirects, host-wide one-request-per-second budget and persistent cooldown. Separate machines require a shared operator-managed gateway.
- Existing notebook exports, Stock Explorer consent, pricing/risk tools and navigation are preserved.

## What is unavailable

No licensed earnings calendar, analyst estimates/sentiment, backend market-price feed, valuation, price targets, fair value, quarterly/TTM analysis, automatic business description or exhaustive risk-factor analysis. A filing date is not an earnings date. Stock Explorer's separate consented display does not supply backend data. Standard annual tags can be absent; international/IFRS/custom tags and financial-sector comparisons have limited suitability. SEC reports are issuer evidence, not independent corroboration.

## Verification — November 5, 2026, Toronto time

A genuine operator contact was supplied privately for testing, never committed. Initial restricted-network DNS failed; the authorized network retry succeeded. Live AAPL directory, submissions and companyfacts retrieval succeeded at 2026-11-06 04:19 UTC. The normalized annual period was 2026-09-26, filed 2026-11-03, accession 0000320193-26-000026; all four compatible ratios were available. The app's real-data browser check subsequently retrieved both AAPL and MSFT and displayed their cards/provenance at desktop and mobile widths. These are point-in-time retrieval checks, not a guarantee of future provider availability.

Automated fixture tests remain explicitly synthetic and separate from production. Full suite: 2,130 passed, 208 existing warnings. Chrome regression covered notebook last-field exports, shared notes, model navigation, consented Stock Explorer panels, independent sessions and 390/400/768/1440px widths. Isolated Discover browser checks covered screening/filtering, missing evidence, failed refresh clearing results, no embeds and 390/768/1440px widths. Ruff, dependency compatibility, whitespace and Bandit medium/high gate passed. No merge or deployment.

SEC interface documentation: https://www.sec.gov/edgar/sec-api-documentation and https://www.sec.gov/developer.

Review captures: [desktop evidence cards](images/discover-live/live-desktop.png), [390px mobile](images/discover-live/live-390.png), [768px](images/discover-live/live-768.png). These show real retrieved SEC evidence, not synthetic issuer examples. Machine-readable browser results are in `docs/discover-live-validation/`.

For an optional repeat browser check, install development requirements (`python -m pip install -r requirements-dev.txt`) and have Google Chrome installed. With the configured app already running at port 8501, use `python qa/discover_live_browser.py --base http://127.0.0.1:8501`. This intentionally makes a bounded real-data scan; fixture-only browser checks use the isolated `qa/discover_preview.py` server instead.
