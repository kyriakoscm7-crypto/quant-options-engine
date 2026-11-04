# Production readiness review — November 3, 2026

## Release decision

**Draft preparation only. No production release authorized.** Work is on `safety/legal-risk-reduction-2026-11`, PR #6. M20 is outside scope. No viewer, hosting, repository protection or production branch settings were changed.

The live Streamlit app inventory was read in the owner's existing browser: `quant-intelligence-km.streamlit.app`, repository `quant-options-engine`, branch **`quant-intelligence-automation`**, entrypoint `dashboard/main.py`. This is NOT evidence that production follows `main`. Do not push to that deployment branch. Verify the final production commit and branch before approving any release. No new preview cloud app should be created without authorization. General settings show Python 3.11. Sharing was inspected read-only: “Only specific people can view this app”, with one explicit invited address corresponding to Michael. The owner is implicit through repository permissions. GitHub collaborators were checked read-only: owner/admin and Michael/write only. A fresh signed-out browser was redirected to a Streamlit denial/sign-in page. No secret values were opened.

## What the app actually does

| Workspace | Inputs and provenance | Limitations |
| --- | --- | --- |
| Opportunity Discovery / Scanner | Official opt-in TradingView screener; curated real-listing shortcuts; exact exchange-qualified custom listings | Provider filtering/sorting stays in its frame. No app ranks, price exports, fundamental feed or claimed predictive edge. Curated list is not comprehensive or automatically refreshed. |
| Discovery shortlist | Up to 50 session-local user records; status, research question, source link, evidence period, counterevidence, review trigger; comparison of up to four records; JSON download | User-authored, unverified research. No market metrics inferred, no automatic URL retrieval. Download before losing the session. No account persistence or import facility. |
| Stock Explorer | Official chart, company, financials, technical and news widgets; separate user notes | External panels may be delayed/unavailable. Chart range and interval are requested independently; provider/user toolbar can alter display. No extraction into models. |
| Quant Lab | Existing Black–Scholes, analytical Greeks, scenario calculations and strategy experiments | Hypothetical European option models; no execution guarantee, liquidity model or brokerage connection. Assumptions and omissions remain visible. |
| Simulation, Forecast and Portfolio Labs | Local model assumptions / deterministic fictional OHLCV | Located under Quant Lab. Fictional forecasts are software examples, not real-company predictions or validation of profitability. Engines preserved. |
| Learn | Educational calculators / illustrative user inputs; external official links | Use invented household amounts. Tax examples are not personalized tax advice. |
| Separate FastAPI | Validated manual numerical inputs, pricing/Greeks/batches/portfolio/scenarios | Streamlit sign-in does NOT protect this service. Legacy market-data HTTP route always returns 403. |

## Repository and request-path inspection

Frontend entrypoint: `dashboard/main.py`. A guard intercepts all six data-sensitive routes before legacy provider-dependent renderers. `dashboard/pages/2_Quant_Discovery.py` applies the same guard when opened directly. `dashboard/public_safety.py` cannot be bypassed with the historical rights flag. `dashboard/demo_showcase.py` dispatches actual display-only discovery/reference pages or clearly fictional portfolio/forecast demonstrations. Existing tests exercise these boundaries with HTTP clients blocked.

The following provider-dependent engines remain development-only: `app/market_data/{yahoo_client,stock_history,multi_expiration,market_sessions}.py`, `app/backtesting/historical_data.py`, `app/forecasting/research_data.py`, `app/discovery/{universe,universe_expansion,ranking_engine,ranking_pipeline}.py`, and their callers. Nasdaq Trader listing downloads, Yahoo/yfinance and Google News RSS (`app/intelligence/news_engine.py`) are not cleared for hosted ingestion/redistribution. SEC requests in `app/intelligence/sec_filings.py` belong to the old event investigation path. CLI scripts are not evidence of licensed use; do not schedule or publish their output without source-specific review.

Read-through included API request models/routes, request safety middleware, mathematical module boundaries, dashboard route dispatch, direct page entrypoint, all network call sites, Docker/build context, requirements, workflow, ignored/tracked datasets, settings/consent/privacy notices, existing regression suites and repository rules. This is a code/behavior audit, not a penetration test or verification of third-party internals.

## Security and privacy findings

- Existing controls: finite numerical input validation, bounded batches and combined scenario work, actual request-body byte counting (including chunked bodies), safe validation errors, numerical-domain errors, no-store/nosniff/referrer response headers, no public market-data API bypass. No portfolio/account uploads in the safe research flow.
- New optional separate API protection: set a strong random **`QI_API_TOKEN`** of at least 32 characters in a host secret store. All HTTP routes except `GET /health` then require a Bearer token; authenticated requests share a 120/minute process budget. Failed auth occurs before body parsing. Duplicate authorization headers fail. No token values or bodies are logged by this middleware. Do not put this token in browser code or Git.
- **Unset token intentionally preserves local calculator compatibility, and leaves the API unauthenticated.** Keep it on loopback/private networking. Never expose the separate API publicly without authentication, TLS, proxy rate/concurrency/time limits and request-size controls. Process limits are not distributed or DDoS protection; multiple workers each have a budget. WebSocket serving is outside this HTTP middleware.
- Container runs as UID 10001, copies only `app/`, and passes a read-only/capability-dropped smoke run. It is a FastAPI image, NOT the Streamlit deployment. No production endpoint was started.
- Research notes are server-memory session state, not browser-only storage or encrypted personal vaults. No `cache_data` stores notes. External panel consent is session-scoped, off initially, and revocable for future loads. Disabling cannot recall prior requests. External links intentionally leave the app and have their own privacy terms.
- Private host sign-in is the access boundary, not a toggle in the app. Explicit viewers **and inherited repository writers/admins** were reviewed: one Michael invite, owner/admin and Michael/write only. Fresh signed-out browsing was denied. An uninvited signed-in identity remains an owner acceptance check. Michael/write inherits management access; no permissions were changed.
- Public GitHub repository confirmed via connector. CODEOWNERS names owner. Read-only GitHub API confirmed strict required CI checks (Python and Docker), one code-owner approval, stale-review dismissal, conversation resolution, no force pushes or deletion. **Administrator enforcement is disabled**, so owner/admin bypass remains possible. Ruleset list was empty. Settings unchanged.
- Requirements have broad version ranges; successful fresh CI/audit is necessary and does not guarantee future resolution reproducibility. No vulnerability immunity is claimed. Dependency pinning/controlled update policy remains a maintenance task.
- Hosting retention, administrators, session cleanup, subprocessors, incident response and actual production secret inventory cannot be established from source. Do not print secrets to verify their existence. Review settings by key name only.

## Residual risk register and release gates

| Severity | Risk / evidence | Required resolution |
| --- | --- | --- |
| Blocker | Live app points at `quant-intelligence-automation`; release branch differs | Owner records target branch/commit and approves exact release; no automatic branch synchronization. |
| Blocker | Private sharing and one invited viewer observed; inherited permissions / anonymous denial require verification | Observed private Sharing, owner + Michael repository access, and signed-out denial; owner reconfirms invite identity and tests an uninvited signed-in identity before release. |
| Blocker | Streamlit Community Cloud terms restrict heightened-protection content including financial information | Confirm project/content eligibility with host. Public-company research and fictitious amounts reduce collection, but are not a hosting exemption or approval. |
| Blocker | Widget/operator terms acceptance and intended use cannot be determined solely from embed docs | Owner reviews intended private noncommercial use; resolve ambiguity with provider. Keep attribution and no extraction. |
| High | Privacy retention/US processing and applicable Canadian provincial/federal duties unverified | Document actual host practices; jurisdiction-specific counsel as needed. |
| High if exposed | Separate API without token/proxy controls | Keep private or configure and test token/TLS/proxy protections before exposure. |
| Medium | Model misspecification / user reliance | Keep hypothetical labels, no recommendation claims; independently verify material calculations. |
| Medium | No authorized backend market price/fundamental feed | Explicitly unavailable. Do not substitute synthetic company metrics or assume derived output is unrestricted. |
| Medium | Session data can disappear; download contains user text | Explain scope, export before leaving, clear session shortlist, store downloads appropriately. |
| Medium | External widget availability / mobile overflow / accessibility | Final target-host desktop/mobile, keyboard and screen-reader checks remain required; third-party UI not controlled by app. |
| Medium | Broad dependency ranges and admin bypass | Review each CI result and owner-controlled merge; plan reproducible dependency updates. |

## Preview and owner approval checklist

1. Stay on PR #6 branch. Run `.venv/bin/python -m streamlit run dashboard/main.py --server.address 127.0.0.1 --server.port 8510` from repository root. This is local preview only.
2. Inspect Discovery with panels off. Add Apple and Microsoft, record different research questions and source periods, compare, export, switch company and route, confirm notes survive. Open the SEC search and verify issuer identity manually. Clear shortlist when done.
3. Opt in once if desired. Check screener, chart, provider attribution, ranges (1D/1W/1Y/All), line/candle style and absent symbols. Confirm Settings disables future external loads. Check narrow/mobile layout and keyboard focus. Provider display state can differ from requested range; never label it an app-verified historical sample.
4. Confirm Forecast/Portfolio simulations live under Quant Lab. Exercise options, Greeks and scenario controls. Confirm fictional/model labels remain visible.
5. Require final-commit CI: full Python tests/lint, dependency audit and Docker build/smoke. Review exact commit in PR, not an older green check.
6. Before production approval: resolve blockers above, verify branch/viewers/anonymous denial, establish rollback commit, confirm no credentials or research exports in diff, and approve a specific commit and target branch. Approval is still outstanding.
7. Only after separate explicit approval: deploy approved commit, repeat host smoke/access/consent checks; revert to recorded last-known-good commit if needed. No host actions are performed by this document.

See [source-rights evidence](SOURCE_RIGHTS_2026_11.md). These are engineering controls and research findings, not legal advice, a registration determination or guaranteed compliance.

## Verification performed

- Full local suite: **1,914 passed**, 208 warnings (primarily pandas deprecations), 86% measured `app` coverage. No claim that UI or integration coverage equals that percentage.
- Ruff now covers **all** `app`, `dashboard`, and `tests` in CI and locally; clean. Git whitespace check clean.
- Live dependency audit: **90 installed packages, no known vulnerabilities found** at review time. This is not assurance against undisclosed vulnerabilities or future dependency resolutions.
- Docker image built locally; nonroot UID 10001, read-only filesystem, all capabilities dropped, no-new-privileges. Loopback health returned healthy; standard European option request returned call 10.4506 / put 5.5735. Temporary container removed.
- Running local browser: Discovery rendered with panels off, actual listing selector and EDGAR link; adding Apple exposed an editable research record and comparison/download controls. Automated Streamlit tests cover route handoff, no backend HTTP, consent reset, notes across rerenders and company changes, fresh-session isolation and clear/re-add. Full provider rendering and mobile/assistive-technology checks on the approved target remain acceptance tasks.
- High-confidence credential-signature scan covered tracked working-tree files and all locally available Git blob history for private-key headers, GitHub legacy token signatures and AWS access-key IDs; 465 historical blobs checked, no matching signatures found. No secret values were read from host settings. This narrow scan is not a comprehensive secret-detector or remote secret-inventory review.
- Final remote CI must be checked for the pushed release-preparation commit. No production settings changed, no merge/deploy performed.
