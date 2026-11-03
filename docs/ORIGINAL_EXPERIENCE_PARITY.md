# Original experience with the current safeguards

Scope: draft PR #6, November 3, 2026. No merge, deployment or hosting/sharing changes.

## Reference and verification limits

Compared the original implementation in `origin/main` (base b2d7295) with the
private-workspace branch. The live application URL is documented as
https://quant-intelligence-km.streamlit.app/ . This follow-up attempted a
read-only visit, which redirected to Streamlit's hosting origin; browser approval
review blocked inspection of that destination because it could expose a signed-in
hosting account. The current live deployment and its exact commit are therefore
**not verified** by this follow-up. Source parity must not be described as a
pixel-perfect match to the site currently running. No hosting/account settings
were inspected or changed.

## Preserve the product, change the source where necessary

| Original capability | Current implementation and boundary |
| --- | --- |
| Premium navy/pink homepage and grouped sidebar | Existing homepage, Learn content, theme and navigation retained; compact Settings added. |
| Stock/ETF search, period, Line/Candlestick controls | Restored compact three-column controls, stacked naturally on phones; simple labels with exchange-qualified internals. Known incoming ticker requests work; unknown listings require an explicit exchange. |
| Summary followed by price chart | Official quote overview and chart open automatically after session consent. 1D through All uses provider ranges separately from candle size. |
| Performance tab and company research | Original tab location restored; official financials and company profile. Provider chart toolbar supports comparisons where available. Original app-computed SPY relative-return cards are not recreated from widget data. |
| Risk & Scores tab | Original tab location restored; official provider technical assessment with clear source. App-computed volatility, beta, drawdown, scores and forecasts need a separately authorized price-history integration. |
| News tab | Official provider news panel; no copied news feed, scraping or invented company headlines. |
| Historical Data tab and CSV | Original tab location retained with an explicit availability explanation and provider link. App price tables/exports remain unavailable without a verified data agreement. |
| Research notes | Additional My analysis tab; per-company session notes, download of user-written text only. Public-company research only; no account details or real holdings. |
| Discovery, Scanner, Forecast and Portfolio | Existing quantitative engines retained in source. Discovery/Scanner now use official real-stock displays. Simulation Lab pairs real-company references with independent models; Portfolio/Forecast remain fictional demonstrations. Portfolio includes the synthetic Monte Carlo lab. Generated models are not company-specific replacements for observed history. |
| Options, Greeks, Scenarios, Strategy and Learn | Existing mathematical and educational interactions preserved with illustrative inputs and assumptions. No brokerage connection or execution added. |

The aim is continuity of navigation, controls, information hierarchy and existing
mathematical work. A disclaimer, login or private guest list cannot grant rights
to extract price data or eliminate financial/privacy obligations.

## Implemented safeguards

- Host-independent data guards remain fail-closed, including direct renderers,
  direct Discovery entry, and the legacy Yahoo HTTP endpoint. An environment
  attestation does not unlock hosted feeds. Regression tests reject server HTTP
  on hosted research routes and bundled market snapshots.
- Provider scripts are fixed official TradingView display widgets, with visible
  attribution. No chart DOM/message/network extraction, proxy, caching or price
  export is added. Market coverage, delay and missing-data notices remain.
- External requests require a disclosed individual session opt-in. All research
  tab widgets are eager, including unselected tabs; first-use copy, Settings and
  Privacy disclose automatic tab-panel loading. Turning off/resetting removes
  every provider embed. Notes work without consent and are not passed to widgets.
- Symbol validation rejects markup and bounds exchange/ticker lengths. Unknown
  exchanges are never inferred from an unqualified navigation request. Notes have
  a 10,000-character limit per field and warn against personal financial details.
- Existing API body/batch limits, generic error responses, response privacy
  headers, non-root container, dependency audit, full tests and Docker smoke CI
  remain in place. This UI change does not establish production rate limits or
  host access control.

## External checks still required before release

These cannot be truthfully completed by repository edits:

1. Owner verifies actual host Sharing settings and current viewers (owner and
   Michael), signed-out denial, invited-account access and administration/MFA.
   No app session flag is authentication. Strict allowlisting may need a suitable
   host/access gateway if the platform permits invited viewers to invite others.
2. Resolve hosting suitability, actual logs/session retention, telemetry,
   subprocessors and cross-border arrangements. Avoid confidential financial
   inputs; the existing hosting-terms concerns remain unresolved.
3. Obtain and document a provider agreement before restoring backend real-stock
   analytics, historical tables/exports, news ingestion or derived forecasts.
4. Assess applicable securities/privacy/consumer rules for the actual activity,
   audience, jurisdiction and any future monetization with qualified advisers.
   Private access does not establish an exemption or legal clearance.
5. Owner explicitly approves merge/deployment; then verify real production
   authentication, mobile layout, widget coverage, consent withdrawal and rollback.

## Primary references

- TradingView data/API/export limitations: https://www.tradingview.com/widget-docs/faq/data/
- Widget attribution and privacy FAQ: https://www.tradingview.com/widget-docs/faq/general/
- Provider privacy policy: https://www.tradingview.com/privacy-policy/
- Consent guidance: https://www.priv.gc.ca/en/privacy-topics/privacy-for-businesses/appropriate-handling-of-personal-information/collecting-personal-information-and-consent/consent/gl_omc_201805/
- Hosting verification and existing audit: PRIVATE_RESEARCH_WORKSPACE.md and END_TO_END_RISK_AUDIT.md.
