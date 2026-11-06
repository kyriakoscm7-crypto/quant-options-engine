# Discover Intelligence v2 — review candidate, November 5, 2026

This feature is proposed against main; no production deployment, merge, sharing
change or provider account change is authorized by this PR. Stock Explorer's UI,
widgets, consent and model handoffs are preserved. Its SEC financial transport
now shares the same host-wide SEC budget as directory, filings and Discover.
No dependency or market-data rights flag is introduced.

## What works

Discover adds company briefs above the existing screening/shortlist workflow.
Choose one to three SEC tickers, build a brief, inspect annual ratios, compare
selected companies, read filing/source links and investigate explicit gaps.
The existing session notebook still supports questions, counterevidence, review
triggers, restore and downloads. It remains session-local. The market screener
is collapsed initially in Discover and retains its explicit provider consent.
The Scanner route retains its original expanded screener.

The backend uses the existing CompanyRegistry to reject ambiguous identities.
SEC ticker identity is a filing-entity identity, not verified exchange metadata;
it is never used to guess a Stock Explorer exchange. The exact selected listing
still drives the existing notebook/Explorer handoff independently.

Financial health supports standard US-GAAP USD facts from 10-K and 10-K/A only.
Full-year duration observations require 330–380 days. Instant balance-sheet facts
must have no start date. All observations use the latest annual period found in
supported duration tags; missing metrics remain missing. Latest filing date wins
for revised historical observations, with a revision notice. Conflicting values,
start dates or accessions on that filing date are excluded. Ratios require the
same accession and start/end context and a positive denominator. Values retain
concept, unit, period, filing date, form, accession and original SEC archive link.
Annual periods older than 550 days are flagged. No health score, price target,
return prediction, custom stock ranking, or personalized buy recommendation exists.
Custom IFRS/issuer tags and quarterly/TTM metrics are intentionally unsupported.
Historical point-in-time backtesting is not offered by this current-facts service.

## Source admission and actual coverage

| Dataset | Implementation | Activation / remaining evidence |
| --- | --- | --- |
| SEC company directory | Exact ticker/CIK lookup, official registered name | Genuine `QI_SEC_USER_AGENT` app/contact identity; review deployment-wide fair access |
| SEC submissions | Recent normalized filing dates, forms, accessions and links; amendments stay separate | Same SEC identity; older paginated history is not fetched |
| SEC companyfacts | Bounded structured numeric facts and dated ratios | Same identity; issuer-reported data, not audited by this application |
| Next earnings | Typed evidence adapter, freshness/identity/rights checks, independent-owner reconciliation, conflict status, timezone/date-only handling and `1d` proximity | **No live provider connected.** Reviewed earnings redistribution/derived-use agreement and provider-specific adapter/key required |
| Analyst sentiment | Attributed provider labels, sample size, as-of time; no app-created consensus or averaging | **No live provider connected.** Licensed analyst dataset and provider-specific rights/attribution/methodology review and adapter/key required |
| Corroboration | Reject stale/future/unsafe/unlicensed/wrong-issuer evidence; count underlying owners rather than syndicated outlets | Tested with explicit synthetic fixtures only; no real multi-source coverage claimed |

`APPROVED_SOURCES` is empty. A key, environment variable or checkbox cannot admit
a provider. A separate reviewed integration PR must register exact contract
reference, dataset owner, display/derived rights, expiration and datasets, plus
contract-specific users/geography, attribution, retention/deletion and quotas.
Do not paste licensed feeds into notebook notes as an ingestion workaround.
No web scraping, TradingView extraction, Yahoo ingestion or copied news consensus
is introduced. SEC submissions and XBRL are the same issuer origin, not two
independent corroborating sources. An earnings filing date is never substituted
for an upcoming earnings announcement.

Calendar proximity is **calendar days**, not a rolling 24-hour countdown. A timed
event is converted to the viewer timezone (America/Toronto default); a date-only
announcement retains its source timezone and explicitly says time unannounced.
DST tests cover the November transition. Estimated and source-confirmed events
remain distinct; disagreements remain visible rather than voting on a winner.

## SEC access and source provenance

Official guidance reviewed November 5, 2026:
- https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- https://www.sec.gov/search-filings/edgar-application-programming-interfaces

Exact endpoints used by Discover:
- `https://www.sec.gov/files/company_tickers.json`
- `https://data.sec.gov/submissions/CIK##########.json`
- `https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json`

Only structured identifiers and financial numeric facts are normalized. Full
filing prose, exhibits, report tables and company logos are not downloaded or
republished. Links lead to the original documents. This implementation is not a
claim that SEC hosting grants rights to third-party exhibits or other datasets.
It supersedes the old register's statement that Discover is link-only for these
three narrowly defined structured endpoints; all other source guards remain.

Discover allows only these fixed resources and numeric CIKs, rejects redirects,
bounds decoded responses to 25 MB, closes responses, uses connect/read timeouts,
retains UTC retrieval timestamps and caches directory data for 24 hours and
company data for one hour (24 entries / 50 MB serialized responses maximum; Python objects add overhead). No stale fallback is represented
as current. Service failures preserve the shortlist and do not substitute metrics.

`sec_access.sec_get` serializes SEC request starts at one per second across
threads and processes of the same OS user on one host, using a locked private
budget file in the host temporary directory. All current SEC HTTP entry points
use it. A 403/429 pauses that budget for at least 600 seconds and honors longer
Retry-After values. There are no automatic retries. The local budget rejects
symlinks and corrupted state; contact identity is not shown in the UI.

**Deployment gate:** this host-local file does not coordinate different hosts,
containers with different temporary files, OS users, or unrelated applications.
Before activating live SEC on a deployed build, inventory all operator traffic
and route it through one shared gateway/budget; total traffic across machines
must respect SEC's aggregate maximum 10 requests/second. Multiple independently
limited replicas are not an approved deployment. An environment flag cannot
attest to aggregate compliance. Existing release/hosting/privacy gates remain.

## Verification and release

See the PR validation section for exact commands/results. Unit and integration
fixtures are synthetic, never evidence that these numbers describe a live issuer.
No live SEC request was made with an invented contact, and no real provider
coverage or contract is certified. CI runs the existing full tests, independent
checks, audit, security scan, secret-history scan, browser regression and Docker
smoke jobs. Review those results for the exact head before merging; this PR does
not deploy. Browser captures are presentation evidence only, not live-data proof.

### Local validation record

Python 3.11.17, fresh disposable environment installed from `requirements-dev.txt`:
- Full suite: **2,118 passed**, 208 existing runtime/deprecation warnings.
- New Discover unit/integration/UI tests: **38 passed** including cross-process
  budget spacing, DST, restatements, license expiry and data conflicts.
- Ruff across CI paths, `pip check`, independent quantitative checks,
  `bandit -r app dashboard -ll`, locked dependency vulnerability audit and
  secret-history scan passed. Whitespace validation passed.
- Real Chrome browser regression passed: actual final-field notebook JSON
  downloads, shared notebook/navigation, independent sessions, six consented
  Explorer panels and responsive checks at 390/400/768/1440 pixels.
- Desktop/mobile brief UI uses **synthetic QA fixtures**, not downloaded issuer
  facts. No live SEC or earnings/analyst provider verification is claimed.

Review captures: [desktop](images/discover-v2/discover-1440.png),
[mobile](images/discover-v2/discover-390.png),
[synthetic company brief](images/discover-v2/brief-synthetic-fixture-1440.png).
Container/remote CI results are recorded on the pull request, separately from
these local tests. Existing release gates still apply to the exact final head.
