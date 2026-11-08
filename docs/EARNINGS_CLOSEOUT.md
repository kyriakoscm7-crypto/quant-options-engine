# Earnings calendar closeout — November 8, 2026

The research-calendar implementation is ready for review on PR #12. No merge or
deployment is included. This is not a certification of universal schedule accuracy.

## Verified against the existing live cache

A read-only inspection found 1,271 normalized provider events for Nov 9–15.
Cisco was listed Nov 11; its official Nov 3 announcement specifies Nov 12 AMC.
TransDigm was listed Nov 11; its official Nov 2 announcement specifies Nov 10 BMO.
Ferguson and Take-Two were present but excluded by the featured shortlist.
Trade Desk was absent despite its issuer-announced Nov 9 AMC release.

The presentation now reconciles reviewed issuer release facts, corrects the two
conflicts and adds the missing Trade Desk event (1,272 displayed weekly events).
It renders 10 initial featured cards from 12 matches, with explicit editorial
priority across all reporting days and Show 10 more. FERG, TTWO and TDG are now
featured. Each issuer-backed card links its announcement; provider-only cards
say they are not issuer-verified. Calendar dates never come from Google AI text.

Only five records explicitly establish release date/session and can reconcile
provider events. Call-only schedules cannot override release timing. Reviewed
release facts expire after 30 days and apply only to their explicit week.
The change adds no network calls or per-card calls and rewrites neither the
provider snapshot nor its durable request ledger. No keys were read or displayed.

## Validation

- Full local suite: 2,244 passed; 223 existing dependency warnings.
- Ruff, dependency compatibility, Bandit medium/high, secret-history scan,
  independent numerical/API checks and whitespace checks passed.
- Chromium 390/768/1440: existing 1,270-event synthetic regression plus a new
  source-correction regression passed.
- Chromium 390/768/1440 using the actual cached snapshot, read-only with the
  provider method mocked to forbid fetching: corrected dates, ten initial cards,
  12-card expansion, FERG/TTWO inclusion, official links, no duplicate CSCO,
  day/search behavior, no horizontal overflow and Research handoff passed.
- Mobile screenshot visually inspected. No live API quota was spent.
- CI outcome for the final commit is recorded on PR #12.

## Scope limits

This is a provider-reported research calendar with a small reviewed issuer layer,
not an automatically issuer-confirmed market-wide schedule. Weekly snapshots can
miss intraweek changes; retrieval time and sources are shown. There is no
market-cap source or measured size ranking. Monthly accounting and shared cache
coordinate processes using one persistent local SQLite file; independent hosts
need a central transactional database before using the same provider key.
No AWS resources, migration, paid source, merge or deployment is included.

Restart Streamlit after pulling to reload imported modules. Do not delete the
cache or change secrets to install this fix. The existing weekly cache remains valid.

## Hosted release mode selected by owner

On November 8 the owner selected release with the limited issuer fallback until
durable cloud storage exists. The calendar UI therefore defaults API coverage
off; `EARNINGSAPI_ENABLED = true` is a separate explicit opt-in for the full
calendar on a durable host/local Mac. Existing credentials alone do not enable
it. The limited schedule, source links, expiry and Research remain available.
GitHub required review remains a separate deployment gate. No merge or deployed
SHA is asserted by this note.
