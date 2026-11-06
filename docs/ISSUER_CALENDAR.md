# Curated issuer earnings schedule

Reviewed November 6, 2026. The seven records in
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
