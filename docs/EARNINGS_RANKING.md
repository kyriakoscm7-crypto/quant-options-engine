# Earnings calendar ordering and display review

Reviewed November 7, 2026. Applies to PR #12.

## Current decision

**No market-cap source is connected. True market-cap ranking is unavailable.**
The default is **Top earnings this week**: up to ten featured provider events,
ranked across every reporting day by editorial prominence. Never pad a sparse
week with companies lacking a provider event or reviewed issuer release fact. Show 10 more reveals
additional featured matches. All week includes the complete event universe,
including weekends; Monday–Friday chips select individual days, even empty ones.
Search covers the full weekly universe, within a chosen day when selected.

Editorial priority v3 (November 8, 2026) is published in
`earnings_ranking.EDITORIAL_PRIORITY` and the UI limitations panel. It reflects
subjective broad investor recognition and earnings attention, not size, returns,
or a measured popularity score. Remaining members of the versioned
`FEATURED_MAJOR_SYMBOLS` set use ticker order; nonfeatured events use date/ticker.
No unverified dates or invented companies/caps are added; reviewed issuer corrections and supplements are sourced per card. No provider requests are added.
No featured matches leaves Top empty with All week available.

Matching trims whitespace, uppercases and equates dot/hyphen share-class notation
(e.g. BRK-B/BRK.B); it does not strip exchange suffixes or equate different share
classes. Original provider symbols and events remain unchanged for Research.
The existing provider normalizer deduplicates by date/ticker and withholds
contradictory sessions before ordering.
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
network call or quota spending in ordering. Current runtime uses `order_featured_events`, never calls this adapter, and
keeps its licensed-cap contract available for a separately reviewed integration.

The guard requires complete coverage of the entire weekly universe, positive
finite values, explicit display authorization, named HTTPS provenance and a
common observation date within four calendar days. That freshness limit covers
weekends but is a conservative display policy, not proof of quote quality.
Partial, stale, inconsistent-date or failed adapters revert the entire calendar
to date/ticker order, so missing caps never imply smaller companies. A future
integration must also display individual value/source provenance before release.

## Interface and validation

Ten two-column cards initially, stacking on narrow screens; Show 10 more;
search across all weekly events; Top/All week/weekday chips; explicit
BMO/AMC/unknown sessions; provider source; distinct accessible Research buttons.
Search, view and week changes reset pagination; background retrieval does not.
The week-scoped choice survives Research navigation and resets on week rollover. Research uses the
existing Stock Explorer ticker request, preserving identity verification there.
Curated issuer fallback and source limitations remain intact.

Synthetic fixtures contain 1,270 entries and never call a provider. Unit tests
cover pagination, full-universe search, day counts, numeric ordering, incomplete
coverage, invalid values, freshness, permission, provenance and adapter failure.
Browser checks cover 390px, 768px and 1440px layouts, widget counts, paging, search,
day filtering, overflow and Research routing. Screenshots are generated under
`/tmp/qi-browser/earnings` and uploaded by the existing CI browser artifact step.


## Featured ordering regression checks

Tests cover cross-week priority, deterministic ordering, membership-only output,
normalization/listing boundaries, combined filters, empty/no-match fallback,
all 1,270 events through incremental paging, and no duplicate cards. Mocked
provider/cache integration proves filtering, ranking and paging spend only the
original seven requests, with an unchanged durable budget. Browser fixtures label
all entries synthetic and assert a Friday featured event precedes Monday events,
BMO/AMC dates, full-universe search, pagination resets, day counts, Research and
no horizontal overflow at 1440 and 390 px. No live calendar or cap calls are made.

## Current source recheck (November 7, 2026)

- https://www.earningsapi.com/docs/calendar-earnings still supplies no cap field.
- https://www.earningsapi.com/terms permits displaying earnings content; it does
  not establish an explicit market-cap data grant. Its Market Caps documentation
  link (https://www.earningsapi.com/docs/marketcaps) currently redirects to the
  general docs without a response contract, currency, coverage or as-of policy.
  No authenticated cap request was made and no entitlement/freshness is claimed.
- https://ranaroussi.github.io/yfinance/ explicitly describes the Yahoo API as
  intended for personal use. Existing Yahoo code is not a cap display license.

Therefore no numbers are shown. The future adapter retains complete coverage,
USD units, source URLs, authorization and common recent as-of requirements.
A future integration must disclose coverage and individual value/provenance,
resolve share classes, and use a bounded batch cache rather than per-card calls.

## Closeout corrections

Nov 8 review found CSCO and TDG provider estimates disagreed with their issuer
announcements. The issuer reconciliation layer corrects them at presentation time,
adds TTD's missing issuer-announced release, and displays official sources.
See ISSUER_CALENDAR.md for evidence and expiry. Membership v2 adds FERG, TDG,
TTWO and COIN. Priority v3 explicitly orders the common weekly names, so this
week no longer silently uses alphabetical fallback for every featured company.
The priority remains subjective editorial judgment, not measured company size.
Provider-only cards are labeled unverified. Full-week coverage is not guaranteed.
