# Curated issuer earnings schedule

Original schedule reviewed November 6, 2026; five release facts reviewed
November 8, 2026. The eleven records in
`app/intelligence/issuer_calendar.py` contain independently written factual
company names, tickers, event dates, release-session descriptions and call times.
Each record links to the primary issuer announcement/events page reviewed using
web search followed by opening the original page. No paid feed, search-result
snippet, article text, logo, analyst estimate or third-party calendar is republished.
No automated issuer scraper or backend network integration was added.

## Evidence

- TTD: issuer press-room announcement dated October 27: November 9 results
  after US market close, call 5 p.m. ET.
- CRWV: October 27 issuer announcement: November 10 call 5 p.m. ET;
  release time not specified in the reviewed announcement.
- AMAT: investor events page: November 12 Q4 earnings conference call;
  no time recorded from reviewed source.
- DIS: issuer Q4 FY26 event page: November 17 webcast 8:30 a.m. ET.
- HD: issuer events page and November 3 announcement: November 17 call
  9 a.m. ET. Do not treat the call as a 9 a.m. results release.
- TGT: issuer events page: November 18 call 8–9 a.m. ET; start shown.
- HPQ: November 3 issuer announcement: November 24 call 5 p.m. ET.

Exact primary source URLs are stored beside each event. No date was inferred
from fiscal-year naming, past schedules, SEC filing dates, or external calendars.
A company-announced event is not a guarantee the schedule will remain unchanged.
Factual extraction with source links does not imply endorsement or a licence to
copy the underlying company documents. No blanket public-release safety claim.

## Maintenance

This is an editorial snapshot, not a live calendar. To refresh, open every
primary source, check for changes/cancellations, add only supported facts and
update REVIEWED after reviewing all retained entries. Use a direct event or
announcement URL where available. Never derive a results-release session from
a call time. Default view is the next 30 days; week filters and company search
apply to this small schedule only. Old events disappear from upcoming views.
After seven days the UI warns that review is due; after 30 days the snapshot is
withheld. Empty views explicitly do not mean no company is reporting.
Finnhub remains disabled and TradingView is a separate broader-coverage link.

## Validation

Regression tests cover date windows, search, past-event exclusion, stale-snapshot
withholding, source metadata, sorting and unknown release times. Targeted UI
tests retain the public provider isolation checks and sidebar flow.

## Release-date reconciliation (November 8 closeout)

Five facts explicitly establish a results-release date/session, separately from
call-only entries: CSCO (Nov 12 AMC), TDG (Nov 10 BMO), FERG (Nov 9 BMO),
TTWO (Nov 9 AMC), TTD (Nov 9 AMC). Exact official source URLs are in each record.
Cisco's newsroom announcement and Ferguson, Take-Two and Trade Desk releases
were opened. TransDigm's issuer announcement was available in search, while its
page returned 403 on direct retrieval; the date is also on its official event
calendar and company-authored PR Newswire distribution. No Google AI overview
was used as source authority.

`reconcile_provider_events` applies these explicit release facts locally after
loading a provider snapshot. A reviewed source replaces all conflicting weekly
rows for that exact ticker, or adds a missing issuer-announced release. Thus the
Nov 8 cached CSCO Nov 11 and TDG Nov 11 estimates become Nov 12 and Nov 10,
respectively, while the missing TTD Nov 9 release is included. Corrections are
counted and each affected card links the issuer announcement. Existing cache
bytes and request ledger are unchanged; no cache purge or extra HTTP is needed.
Only matching explicit week dates are admitted, for 30 days after RELEASE_REVIEWED.
Call-only entries cannot replace a release date or imply a BMO/AMC session.

This is a limited reviewed supplement, not automatic issuer verification of
1,271 provider events. Other cards remain explicitly provider-reported and
unverified. No claim of universal accuracy, completeness or ongoing human review.
