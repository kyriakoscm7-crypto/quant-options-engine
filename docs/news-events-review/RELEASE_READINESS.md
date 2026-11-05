# PR #9 release-readiness audit — November 5, 2026

**Decision: keep draft; not ready for public/commercial news release. No merge or deployment.**

## Branch and preservation

Remote references were refreshed during this audit. PR #9 starts at `cd40a4c`, based
on `feature/quant-intelligence-next` at `82da50a`. Current `main` is `b2d7295` and is
an ancestor of that base; the base is 57 commits ahead, with 83 changed files
(6,282 additions / 2,555 deletions relative to main). The original PR contains 26
changed files / 2,615 additions relative to its selected base.

This is an appropriate stacked development PR: the company-research workflow and
new dashboard are already in the base. Retargeting to main would expand review to
the entire development stack. Keep this base while reviewing the prerequisite
branch separately; eventually re-evaluate against the then-current release branch.
It is not an approval of all 57 prerequisite commits. The local `origin/HEAD`
symbolic reference still names the feature branch, while GitHub reports main as
the default; a stale local symbolic ref does not define the release target.

Edits are confined to the existing `news-events` checkout on the PR head branch.
The sibling `repo` checkout is clean at `f31774e`. The original checkout at
`/Users/Kyriakos/Projects/quant-options-engine` still has its local-only Phase 1–10
modules, tests and backup files; it was inspected read-only. No reset, force push,
production setting change, credential change, merge or deployment was performed.
Hosted production branch/configuration was not independently attested.

## Diagnosed regressions and fixes

- Base commit `cb3ab4c` deliberately replaced the Stock Explorer view selector with
  an open layout, but also removed the `_render_notes` call. Restored that call in
  the existing layout. The browser test still verifies shared notebook revisions,
  final-field export bytes, model navigation and session isolation.
- Updated obsolete Research view and dashboard Options selectors. Six official
  panels now mount after explicit consent; zero mount before consent. The old
  one-panel performance property no longer describes this base's design. This is
  an explicit behavior change in the prerequisite branch, not a disabled test.
- Google RSS now detects 429 before raising a generic HTTP error, closes failed
  responses, and participates in provider cooldowns. Google, GDELT and submissions
  respect numeric and HTTP-date Retry-After values. Provider request serialization
  prevents concurrent different-company requests bypassing a freshly set cooldown.
- SEC directory failures no longer retry on every Streamlit rerender: minimum
  five-minute cooldown for 429, honoring longer Retry-After, and 30 seconds for
  other failures. Bounded stale data remains explicitly labeled.
- GDELT `seendate` is first-seen time, not proven publication time. Metadata and UI
  now retain that distinction. Publication freshness remains unverified for GDELT.
- Report build time is distinct from source retrieval age. Stale/unavailable
  warnings appear beside the report, not only inside its diagnostics tab.
- SEC optional malformed description arrays no longer crash filing rendering.
- Retained navy/white/#FF78B7 theme; placed date/window controls side by side on
  desktop, stacked on mobile; shortened build timestamps and exposed source state.
- Added reproducible offline news preview/browser checks to CI, covering available,
  stale, unavailable, empty and disabled states at desktop/mobile widths, official
  filing URLs and changed-company invalidation. Fixtures are visibly illustrative,
  block external browser requests, and are not routed into the user application.

## Live coverage evaluation and metrics

At approximately 00:06 Toronto time, a bounded GDELT probe requested Apple Inc.,
7-day window, limit 75. It returned HTTP 429. All five remaining queries were
cancelled; no immediate retry or alternate IP was used. Google was not queried
because no affirmative redistribution permission was established. Both application
news providers remain default-off; the local app environment has neither enabled.
No production environment or private contract register was inspected.

| Intended cohort | Planned companies | Requests completed | Usable article sample |
|---|---|---:|---:|
| Large company | Apple, Microsoft | 1 (429) | 0 observable; provider result unknown |
| Smaller-company candidates | Celsius, Turtle Beach | 0 (cancelled) | unavailable |
| Ambiguous name | Block, Gap | 0 (cancelled) | unavailable |

The size labels are sampling intentions, not verified current market-cap bands.
Celsius is not certified small-cap; Turtle Beach's HEAR ticker was absent from the
live SEC directory. A release benchmark must replace absent identities and verify
current market caps from an authorized source before assigning size cohorts.

**Live precision: N/A. Recall: N/A. Publication freshness: N/A. Duplicate rate: N/A.**
There are zero successfully retrieved/labeled live articles and no independent
reference corpus. A 429 is an unavailable measurement, not evidence of zero news.
`qi-live-coverage.json` records all six planned queries and their distinct statuses.
Deterministic fixtures verify mechanisms; they are not real-world accuracy evidence.

Required reproducible benchmark once access/rights permit:

- Freeze exact UTC window, SEC name/CIK, query, source, result cap and source status.
  Use at least two independently verified companies per cohort and disclose every
  per-company article/reference count and any truncation. Six companies are only
  a pilot, not a statistically representative coverage claim.
- Independently label identity relevance against linked publisher/issuer evidence.
  Precision = relevant accepted articles / all accepted articles. Report uncertain
  labels separately and use confidence intervals; no denominator means N/A.
- Build an independent, date-bounded issuer/publisher reference set. Recall =
  recovered relevant reference stories / all relevant reference stories. Query
  yield or classifier agreement is not recall; broader market-wide recall remains
  unknowable from these feeds alone.
- Publication freshness: verified publication-age median/p95 and fraction within
  24h/7d, with timestamp-valid N and unknown N. Report GDELT first-seen ages
  separately; do not substitute them for publication dates or ingestion latency.
- Deduplication: input N, unique story N, removed N/input N, duplicate survivors and
  false merges after human review. Current exact URL/headline matching does not
  establish semantic/syndicated-story deduplication or strip tracking parameters.
- Space low-volume calls, cache results, honor provider Retry-After, and stop the
  provider run on 429. Store unavailable observations as null, never zero recall.

## Provider permissions — official-source review

| Provider/path | Evidence and assessment | Release decision |
|---|---|---|
| Google News RSS backend headlines | [News-specific terms](https://www.google.com/intl/en_us/terms_google_news.html) restrict personal/noncommercial use and public reformatting; that page is dated 2006. [Current general terms](https://policies.google.com/terms?hl=en-US) retain third-party content rights. No current affirmative grant or separate agreement for this app was found. | Keep off. An arbitrary rights-reference string is an operator record, not verified permission. Obtain applicable written display/caching/commercial rights before enablement. |
| GDELT DOC metadata | [GDELT terms](https://gdeltproject.org/about.html#termsofuse) permit commercial dataset use and redistribution with citation/link. [DOC API documentation](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/) expressly supports JSON/custom interfaces. This establishes provider-level dataset reuse; it does not prove all underlying publisher headline/content rights for every audience/jurisdiction. | Keep optional/off pending exact display/content scope review and a successful coverage pilot. Added citation/link in source diagnostics. No article bodies/images fetched or republished. |
| SEC directory/submissions metadata and official links | [SEC Webmaster FAQ](https://www.sec.gov/about/webmaster-frequently-asked-questions) allows reuse of government-created and EDGAR public filing content; declares maximum 10 requests/sec and requires declared identity. | Metadata/link integration supported subject to fair access. No blanket claim about third-party marks/exhibits or legal immunity. Aggregate rate budgeting across directory/submissions, workers and IP traffic remains a release-scale gate. |
| Existing TradingView-hosted news panel | [Official timeline widget](https://www.tradingview.com/widget-docs/widgets/news/top-stories/) and [terms](https://www.tradingview.com/policies/) support the existing attributed provider-hosted display approach, not backend extraction/redistribution. User consent remains required. | No feed ingestion/enablement change. Exact commercial use/hosting eligibility remains an operator review gate documented in the base. |

This is an engineering evidence register, not legal clearance. No agreement was
accepted and no provider was enabled. Public endpoint access and a text field do
not confer display rights.

## SEC linkage, freshness and outages

Live directory: 10,409 records. Five fetched submissions responses matched the
resolved company CIK, including Apple 0000320193, Microsoft 0000789019, Celsius
0001341766, Block 0001512673 and Gap 0000039911. Latest returned filing dates were
November 3–4, 2026; this is a snapshot, not proof of maximum indexing latency.
HEAR returned no directory identity. Raw filing bodies were not downloaded.
See `qi-live-sec.json` for identifiers and dates.

The integration directly requests resolved CIK submissions and rejects a different
response CIK. Regression tests prove rejection/response closure. Filing links use
the selected CIK, validated accession and document path. An accession's first ten
digits may identify a submitting agent, so equality with issuer CIK is not assumed.
Only recent submissions are searched, capped at 100; archive coverage is absent.
Filing date is not acceptance/publication time, and same-day timing stays unverified.

Directory cache: 24h fresh, at most seven days stale. Submissions/news cache: 15m
fresh, at most one day stale. Stale/unavailable status and source cache age are
shown. Tests cover cached and expired data, rate limits, invalid identity, provider
isolation, and outages; 10 browser scenarios exercise all report states. There is
no multi-worker/shared-IP fair-access coordinator yet, and process restarts clear
cooldowns. Do not claim multi-worker production readiness.

## Original PR file-by-file audit

All 26 original changed files were inspected, with tests evaluated against their
implementation and runtime behavior. No original financial-model change is present.

| File | Finding / disposition |
|---|---|
| app/intelligence/company_directory_service.py | Bounded fresh/stale registry; added retry suppression. |
| app/intelligence/company_identity.py | Valid positive ten-digit CIK range and ambiguity rejection; normalization does not verify exchange. |
| app/intelligence/company_intelligence_pipeline.py | Explicit aliases and likely/review split; retained development interface, no new UI predictions. |
| app/intelligence/company_news_relevance.py | Conservative exact-name heuristic; shortened names/punctuation can reduce recall. No factual truth score. |
| app/intelligence/company_registry.py | Search rankings and collision-aware resolution; explicit company/security confirmation, not global listing certification. |
| app/intelligence/gdelt_news.py | Bounded response, safe links, opt-in adapter; fixed timestamp semantics/Retry-After. |
| app/intelligence/news_events.py | Rights gate, isolated sources, CIK-checked submissions, exact deduplication; improved timestamp propagation/429 wait. |
| app/intelligence/news_reliability.py | Bounded cache/deep copies/stale limits; strengthened cross-query cooldown serialization and provider wait. |
| app/intelligence/news_service.py | Legacy GDELT path default-off; injected loaders restricted to developer/test use. |
| app/intelligence/sec_company_directory.py | Bounded download/declared identity; added 429 recognition. |
| dashboard/market_research_workspace.py | Three-line Discovery integration; existing notebook/navigation retained. |
| dashboard/news_events_panel.py | Explicit connection, confirmation, report invalidation; added visible freshness/outage states and responsive control polish. |
| docs/news-events-review/README.md | Original evidence is historical; linked this superseding audit. |
| docs/news-events-review/news-1440.png | Original illustrative desktop evidence retained; current captures are in release folder. |
| docs/news-events-review/news-390.png | Original illustrative mobile evidence retained; current captures are in release folder. |
| tests/test_company_directory_service.py | Fresh/cache/stale/expiry/empty/failure scenarios; new audit tests extend cooldown behavior. |
| tests/test_company_identity.py | Positive mappings, share classes, malformed symbols and ambiguity. |
| tests/test_company_intelligence_pipeline.py | Likely/review/unmatched, no invented aliases, separate companies, unavailable vs empty. |
| tests/test_company_news_relevance.py | Twelve fixture cases including apple farming, pineapple and Block ambiguity; not a live benchmark. |
| tests/test_company_registry.py | Search ranking, duplicate records, collisions and exchange uncertainty. |
| tests/test_gdelt_news.py | Bounded parsing, future/old/unsafe rows, query operators and 429 closure. |
| tests/test_news_events.py | Rights-before-network, provider isolation, duplicate detection, dates/URLs, CIK range and default-off. |
| tests/test_news_events_ui.py | Offline search/report/company change using Streamlit AppTest. |
| tests/test_news_reliability.py | Concurrent dedup, stale/expiry, isolation, cooldown and deep-copy behavior. |
| tests/test_news_service.py | Cache identity, bounds, empty vs unavailable and stale fallback. |
| tests/test_sec_company_directory.py | Declared contact, size limits, invalid JSON and mocked directory download. |

Follow-up files: source fixes listed above plus `news_engine.py`, `sec_filings.py`,
`stock_explorer_widget.py`, `qa/browser_acceptance.py`, new
`tests/test_release_readiness.py`, `qa/news_events_preview.py`,
`qa/news_events_browser.py`, CI workflow and this evidence. No dependencies changed.

## Validation and remaining release gates

See accompanying logs/results/screenshots. Original-head GitHub Docker jobs passed;
the original test job reached browser QA and failed on the removed Research view
selector. Local final results and new-head CI status are recorded below when available.

Remaining gates: successful authorized live news benchmark with real labeled samples;
exact provider/publisher public/commercial display rights; SEC aggregate fair-access
budget appropriate to hosting topology; review/release of prerequisite branch and
exact final CI head; owner approval before any merge/deployment; host/access/privacy
requirements from the existing external-review register. Browser viewport emulation
is not physical-device or assistive-technology certification. No unsupported AI
forecast or price prediction was added.

### Verified local results

- Full Python 3.11 suite: **2,074 passed**, 208 warnings; application/dashboard
  aggregate coverage **75%**. Nine new audit regression cases pass.
- Ruff across configured app/tests/dashboard/QA/scripts: passed. Diff whitespace:
  passed. `pip check`: passed. No dependency changes.
- `pip-audit -r requirements.lock`: **no known vulnerabilities found** against the
  live advisory service. This is a point-in-time dependency check, not a guarantee.
- Bandit full app/dashboard at CI's medium/high threshold: passed; **0 medium,
  0 high, 7 low** findings remain. No suppression added.
- Secret-history scanner: no selected high-confidence patterns in 127 reachable
  commits. This checks configured patterns, not every possible secret.
- Independent checks: 500 numerical cases and API containment checks passed.
- Main browser regression: passed, including real JSON downloads, shared notes,
  model handoff, consent and independent sessions. 390/400/768/1440 widths passed.
- News browser: **10/10** offline scenarios passed (5 states × 2 widths), with no
  horizontal overflow. Screenshots are explicitly illustrative, not live coverage.
- Local Docker image build passed. Read-only, dropped-capability container passed
  missing-token rejection, health/auth, calculation and legacy-feed HTTP 403 smoke
  tests. Test container removed. Image was built from the audited working tree,
  labeled `cd40a4c-audit-working-tree`; it is not a deployable release attestation.
  Image ID is in the smoke log. Final GitHub CI must bind the final commit to its
  own build and release record before release.

Evidence directory: [logs, live observations and screenshots](release-2026-11-05/).
