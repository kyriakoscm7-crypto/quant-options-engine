# Public portfolio preparation — November 6, 2026

First reviewable increment on `feature/discover-intelligence-v2`, PR #12.
No merge, deployment, private duplicate, history rewrite or provider purchase.

## Inspection and scope

PR #12 was open, unmerged, based on main `903007b`, head `52cf9d7`.
Its existing remote CI run 42283858210 succeeded. Local branch initially matched
that head with a clean working tree. Other local and remote feature/audit/backup
branches were inspected and preserved. CI contains test/security/browser and
Docker gates; no deployment job. The live Streamlit URL could not be fetched
by the web inspection tool, so deployed SHA, viewer access and hosting settings
remain unverified. Repository history is not proof of deployed behavior.

All 13 visible route states rendered without exceptions in Streamlit AppTest:
Dashboard; Stock Explorer; Find stocks; Reading earnings; Options; Greeks;
Scenarios; Strategy Research; Simulation; Forecast; Portfolio; Learn; About.
Measured local initial renders were 0.13–0.93 seconds with no live SEC requests;
these are smoke timings, not load or production performance measurements.

## Changes

- Finnhub's service entry point unconditionally clears cached results and returns
  unavailable. No HTTP implementation remains. Credentials, personal_local and
  written_agreement cannot enable it. Historical parsing helpers and Git history
  remain; this is not a private application fork.
- Google News RSS and GDELT production configuration also stays disabled,
  regardless of rights-reference environment strings. No unverified provider
  attestation enables public headlines. Offline injected test loaders remain.
- Reading earnings replaces inactive weekly controls with a report-reading
  checklist and routes to Find stocks and Learn. No invented event dates.
- Find stocks explains the novice workflow and why annual accounting factors
  do not establish valuation, expected return or safety.
- About describes SEC provenance, missing evidence, independent quantitative
  models, architecture and limitations. Sidebar/policy labels identify a public
  portfolio preview. Example secrets no longer solicit Finnhub configuration.
- Existing SEC factors, filings, notebook, chart consent, model experiments,
  pricing calculations and API isolation were preserved.

## Source boundary and dated evidence

Reviewed official sources November 6:

- https://finnhub.io/terms-of-service — redistribution includes derived results;
  third-party sharing requires written approval. No approval is supplied here.
  Consequently the adapter is disabled rather than relying on a setting.
- https://data.sec.gov/ and https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
  — public structured SEC APIs subject to fair access. Existing bounded SEC
  gateway and provenance tests remain. This is not a licence to republish filing
  exhibits or third-party prose. Genuine operator identification is required.
- https://www.tradingview.com/policies/ and
  https://www.tradingview.com/widget-docs/faq/general/ — preserve official widget
  attribution and provider-supported embedding. Browser-only, consented displays
  remain isolated from backend models and exports. Availability and exchange
  rules vary. No blanket redistribution clearance is asserted.

Legacy Yahoo API remains unconditionally 403; legacy market analytics routes
remain intercepted by public guards. No new live provider or derived dataset
was admitted. See source-rights and release-review documents for outstanding
host/provider questions. This revision is not a declaration that release is safe.

## Verification

- Final full pytest: **2,201 passed**, 223 existing dependency warnings (30.10 seconds).
- Ruff, dependency compatibility, Bandit medium/high checks, independent checks,
  secret-history scanning and whitespace validation are run locally.
- Actual Chrome: keyboard sidebar routing and focus; Reading earnings; notebook;
  Stock Explorer; no document overflow at 390/768/1440 px. Mobile screenshot
  inspected. Existing browser acceptance also passed note exports, final-field
  saving, shared notebook navigation, model handoff, six consented widget frames,
  independent-session empty notebook and widths 390/400/768/1440.
- Screenshots and machine-readable browser results are local under
  `/tmp/qi-public-browser` and `/tmp/qi-public-acceptance` (not public artifacts).
- No production secrets or real user notes were used for QA.

## Still unfinished / review gates

This first increment does not finish the entire website. Further work:

1. Audit populated live SEC scans, company comparison, filing evidence and error
   recovery in browsers using genuine operator contact; no contact was invented.
2. Broaden real-browser walkthroughs of every Learn pathway, exercises, all
   advanced lab controls, keyboard-only use, screen-reader labels and contrast.
   Route smoke tests do not establish complete accessibility or correct lessons.
3. Review educational content and simplify advanced evidence presentation further;
   inspect loading/error states and small-screen tables on real devices.
4. Verify final remote CI, dependency vulnerability audit and Docker build gates;
   local checks do not substitute for CI. No new load test or benchmark claim.
5. Verify actual hosting eligibility, logs/retention, deployed SHA, visitor access
   and provider/widget conditions before any release. Existing production may
   still use earlier code. User review is required before merge/deployment.

## Mac review

From the existing checkout, with dependencies installed:

```sh
source .venv/bin/activate
python -m pytest tests -q
python -m streamlit run dashboard/main.py --server.address 127.0.0.1 --server.port 8503
```

Open http://127.0.0.1:8503. Check Discover → Find stocks → Reading earnings,
Learn, Research, Quant Lab, Model testing and Settings → About/Privacy.
Test narrow and wide windows, keyboard Tab/Enter, notes save/export, and chart
consent on/off. Reading earnings must show no dates, API-key prompt or calendar
controls, including if old Finnhub environment variables remain set.
For real SEC research set QI_SEC_USER_AGENT to the project's genuine operator
identity/contact locally before starting; never commit that value. Check filing
periods, source links, missing-data notices and company identity. No Finnhub key
is needed or accepted in this build. Do not enable personal provider feeds for
an employer demo. Leave merge/deployment for review.

## Earnings-calendar follow-up

The Discover sidebar now labels this page **Earnings calendar**. Its primary
button opens TradingView's US earnings calendar in a new tab:
https://www.tradingview.com/earnings-calendar/?countries=us . The destination
was verified against TradingView's live official page. The report checklist
remains below it. No calendar data is copied, fetched by the backend or embedded
through an undocumented widget. Finnhub remains disabled. Targeted earnings and
navigation tests: 11 passed; Ruff and whitespace checks passed.

## Company-sourced calendar follow-up

The page now includes seven real company-announced earnings events directly
in the app, with search, week/30-day filters, source links, separate release
and call timing, checked date and stale-snapshot controls. This supersedes
earlier statements that only the TradingView link is offered. See
[issuer schedule evidence and maintenance](ISSUER_CALENDAR.md). No live provider
feed or automatic issuer scraping was added.
