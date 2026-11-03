# Real-company research: implementation and release review

Reviewed November 3, 2026 for draft PR #6. This is an engineering/source review,
not a legal opinion, a finding of regulatory exemption, or permission to deploy.

## What this update restores

- Discovery and Scanner show actual stocks in TradingView's official screener,
  with provider filters/columns/sorting, attribution, delay/source notices and a
  company-research handoff. No fictional company selector or synthetic ranking
  appears in these hosted routes.
- Simulation Lab provides an actual-company reference selector and official
  quote/chart displays. Independent user-adjustable models remain useful for
  growth, volatility, correlation, allocations, option pricing and Greeks.
  No fictional company list remains in this route. Generated paths retain Model
  A/Model B labels and explicit hypothetical assumptions. Selecting a real company
  never changes or relabels generated metrics as that company's history/forecast.
- The original-layout Stock Explorer follow-up is included in the same draft.
- Forecast and Portfolio remain explicitly fictional demonstrations. This update
  does not restore company-calibrated forecasts, actual holdings, bespoke real-stock
  scores or price-history exports. Their original calculation engines remain in
  source for a separately authorized data integration.

## What is supported by the primary sources

| Source, checked today | Finding and implementation consequence |
| --- | --- |
| [TradingView official stock screener demo](https://www.tradingview.com/widget-docs/widgets/screeners/screener/demos/stock/) | Provides the screener embedding code. Use its `market: us`, `defaultColumn: overview`, `defaultScreen: most_capitalized`, toolbar and provider script; retain attribution. Styling/size use the offered widget configuration. |
| [TradingView data FAQ](https://www.tradingview.com/widget-docs/faq/data/) | Widgets are not an API for retrieving prices or indicator values. Coverage/delay/entitlements vary. No app-side extraction or custom model ingestion. |
| [TradingView terms, section 3](https://www.tradingview.com/policies/) | Display-only permissions do not authorize non-display processing, algorithmic decisions or risk-management use of provider content. Models do not consume widget data. Review actual intended audience/business use against terms; official embed availability is not universal legal clearance. |
| [TradingView general FAQ](https://www.tradingview.com/widget-docs/faq/general/) and [privacy policy](https://www.tradingview.com/privacy-policy/) | Provider metadata/analytics and attribution remain relevant on every page. One versioned session opt-in covers charts, screeners and research tabs across the app; a prior chart-only choice must be renewed, and withdrawal removes current embeds. No third-party prices are imported into server models. |
| [OPC meaningful-consent guidance](https://www.priv.gc.ca/en/privacy-topics/privacy-for-businesses/appropriate-handling-of-personal-information/collecting-personal-information-and-consent/consent/gl_omc_201805/) | Explain the disclosure and give the affected viewer a meaningful choice. Owner authorization/private login does not document Michael's choice. Applicable federal/provincial rules still need activity/jurisdiction assessment. |
| [AMF financial-content guidance](https://lautorite.qc.ca/en/professionals/finfluencers) and [CSA/CIRO guidance announcement](https://lautorite.qc.ca/en/general-public/media-centre/news/fiche-dactualites/csa-and-ciro-provide-guidance-for-finfluencers-and-firms-on-how-to-work-with-them-and-protect-investors) | Education, advice, recommendations and registration depend on actual activities. No personalized recommendation, execution, return guarantee or claim of validated predictive accuracy is added. This app is not automatically classified by the finfluencer guidance; it is relevant risk context for any publication/promotion. |
| [Streamlit Community Cloud terms](https://streamlit.io/terms-of-use), Community Cloud special terms | Restrict sensitive financial information and other protected content. Whether the proposed public-market displays/calculators fit this hosting contract is not resolved by a private viewer list or disclaimer. Do not enter confidential financial data; obtain hosting clarification or use suitable hosting before release. |

## Researched route to the original bespoke real-stock analytics

An API that responds successfully is not evidence of a licence for two viewers.
No API credentials, purchases, accounts or unverified free feeds are introduced.

- [Massive's app-use explanation](https://massive.com/knowledge-base/article/which-plan-do-i-need-to-show-massive-data-in-my-app)
  explicitly says showing data/derived figures to anyone else, including a friend,
  tester or invite-only user, requires Business. Its
  [Business terms](https://massive.com/legal/businesses-terms-of-service) describe
  authorized-user display and derivative analyses within purchased entitlements,
  order forms and third-party agreements. This is a viable candidate to investigate
  for historical feeds and derived analytics, not an acquired entitlement.
- [Alpha Vantage terms](https://www.alphavantage.co/terms_of_service/) default to
  personal/non-commercial use unless agreed otherwise in writing. Its
  [API documentation](https://www.alphavantage.co/documentation/) directs commercial
  use to sales. Do not treat a premium retail key as clearing hosted/multi-user use.
- [Market Data redistribution policy](https://www.marketdata.app/docs/account/data-policies/data-redistribution/)
  distinguishes personal plans from commercial display. Its display permission
  alone should not be read as clearing all custom analytics, exports or non-display
  uses without confirming the intended operations.

For any chosen provider, verify in writing: owner and Michael as intended users,
Canadian location, hosting/display, source/exchanges/delay, adjusted OHLCV history,
server processing, custom scores/forecasts, derived-output display, caching,
retention, export restrictions, attribution and termination. Costs and detailed
entitlements are not approved or purchased by this change.

## Safeguards and release status

**Implemented:** hardcoded official scripts/attribution; per-session explicit
external opt-in and reset/withdrawal; no company/model data coupling; bounded and
validated custom symbols; company handoff without exchange guessing; no backend
HTTP on hosted research routes; legacy Yahoo API remains denied; existing
API/body/error protections, full tests, dependency audit and non-root Docker CI
remain. CI lint includes the new research workspace.

**Still requires external verification before release:** actual host private
sharing/current invited viewers and signed-out denial; host contract suitability;
actual telemetry/log/session retention and cross-border processing; any
provider entitlements for future custom analytics; applicable securities/privacy
rules for the actual activity/audience; explicit owner approval to merge/deploy.
These are not application settings and no settings were changed on the host.

The observed live-site redirect and blocked hosting-account inspection from the
previous follow-up still limit verification of the currently deployed version.
Do not claim this draft's safeguards already protect the live application.


## Validation of this implementation

Full local suite: 1,903 passed, with 208 existing numerical/deprecation warnings.
Ruff and diff whitespace checks passed. Regression tests cover real-company
screening without server HTTP, direct-page guards, default-off/withdrawal/reset,
renewal of older consent, cross-page consent scope, exact company handoffs and
company-independent model results. Desktop browser confirmed actual-stock
screener rows and company-reference/model sections. A 390px phone preview showed
the provider screener fitting the container, with its own horizontal table
navigation. Existing CI runs the full suite, dependency audit and Docker health
checks on push; final commit results must be checked separately. No deployment,
production access verification, licence purchase or professional legal opinion
is claimed.
