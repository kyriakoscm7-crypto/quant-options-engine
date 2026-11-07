# Earnings calendar ordering and display review

Reviewed November 7, 2026. Applies to PR #12.

## Current decision

**No market-cap source is connected. True market-cap ranking is unavailable.**
The default is explicitly labelled **Date, then ticker**, not largest first or a
large-cap subset. No issuer size assertions, estimated valuations, investment
scores, or alphabetical ordering disguised as capitalization ranking are used.
The first 10 are the first calendar events under that ordering.

## Architecture and source investigation

- `earnings_api_provider.py` normalizes symbol, name, date, session, EPS estimate
  and revenue estimate; no market cap is supplied in the current contract.
  The SQLite shared cache, seven-call automatic week batch, durable monthly
  quota, failure cooldown, credentials and Friday rollover remain unchanged.
- Existing `app/market_data/yahoo_client.py` and `stock_history.py` use yfinance.
  Their existence does not establish public display rights for a new cap feed.
  They are not called by this calendar. TradingView stays an external link only.
- FMP offers market capitalization, but its own terms and public-app guidance
  require a specific display/licensing agreement. An ordinary API subscription
  does not establish permission. No such entitlement was verified in this task.
  https://site.financialmodelingprep.com/terms-of-service
  https://site.financialmodelingprep.com/insights/platform/can-you-use-fmp-data-in-a-public-app-website-or-client-dashboard
  https://site.financialmodelingprep.com/faqs
- Alpha Vantage grants personal/noncommercial use unless otherwise agreed in
  writing. No written public-display agreement was verified.
  https://www.alphavantage.co/terms_of_service/
- SEC Company Facts supplies filed XBRL disclosures, with varying period dates;
  it is not a comparable current quote/market-cap feed. The repository has no
  verified display-authorized, same-date price coverage for all earnings
  issuers, with share-class/ADR/currency reconciliation. Multiplying a stale
  shares figure by a Yahoo price would not resolve these issues. No SEC-derived
  approximate cap is calculated.
  https://www.sec.gov/search-filings/edgar-application-programming-interfaces

## Future adapter

`earnings_ranking.RankingAdapter` is an injectable pure ordering interface, not
an enabled provider or an environment switch. A future licensed integration must
supply complete issuer-equity USD values, resolved listing identities, attribution
URLs and dates, after its public-display agreement is reviewed. There is no
network call or quota spending in ordering. Current runtime passes no adapter.

The guard requires complete coverage of the entire weekly universe, positive
finite values, explicit display authorization, named HTTPS provenance and a
common observation date within four calendar days. That freshness limit covers
weekends but is a conservative display policy, not proof of quote quality.
Partial, stale, inconsistent-date or failed adapters revert the entire calendar
to date/ticker order, so missing caps never imply smaller companies. A future
integration must also display individual value/source provenance before release.

## Interface and validation

Ten two-column cards initially, stacking on narrow screens; Show 10 more;
search across all weekly events; all-days/date selector with counts; explicit
BMO/AMC/unknown sessions; provider source; distinct accessible Research buttons.
Search, day, week or retrieval changes reset pagination. Research uses the
existing Stock Explorer ticker request, preserving identity verification there.
Curated issuer fallback and source limitations remain intact.

Synthetic fixtures contain 1,270 entries and never call a provider. Unit tests
cover pagination, full-universe search, day counts, numeric ordering, incomplete
coverage, invalid values, freshness, permission, provenance and adapter failure.
Browser checks cover 1440px and 390px layouts, widget counts, paging, search,
day filtering, overflow and Research routing. Screenshots are generated under
`/tmp/qi-browser/earnings` and uploaded by the existing CI browser artifact step.
