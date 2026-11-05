# News & Events Intelligence review

Implemented on `feature/news-events-intelligence`, based on feature branch commit
`82da50a`. The original checkout at `~/Projects/quant-options-engine` contains
untracked Phase 1–10 work. Its ten intelligence modules and nine tests were copied
into an isolated checkout and preserved as the starting point; the original files
and audit checkout were not modified. Invalid CIKs are now rejected and legacy
GDELT retrieval is explicitly opt-in.

## User workflow

Opportunity Discovery → News & Events Intelligence → enable connections → search
SEC company name or ticker → confirm company/security → build report.
The existing navy, white and pink Streamlit theme is reused. Company selection,
lookback or filing-date changes hide the previous report until rebuilt.

The directory caches for 24 hours, with a bounded seven-day stale fallback.
News and recent SEC submissions use bounded process-local caches (15 minutes
fresh, one day maximum stale), provider cooldowns on HTTP 429 and isolated
provider failures. Source status, cache age and retrieval time are displayed.
Submissions use the resolved CIK, check response identity and bound download size.
Filings include official source links; headline links and timestamps are validated.
Duplicate URL/headline records are removed across sources. Raw article bodies are
never fetched. Unmatched headlines retain their explicit identity warning.

## Operator configuration

- `QI_SEC_USER_AGENT`: application name and real administrative contact email.
- `QI_GOOGLE_NEWS_ENABLED=true` plus `QI_GOOGLE_NEWS_RIGHTS_REFERENCE`.
- Optional `QI_GDELT_ENABLED=true` plus `QI_GDELT_RIGHTS_REFERENCE`.

News providers are disabled by default. Rights references must point to an actual
reviewed agreement or documented permission covering the intended headline display
and audience. These settings record an operator decision; they do not establish
legal permission automatically. Restart the app after configuration changes.
Do not enable a provider merely because its endpoint is accessible.

Provider adapters accept an injected callable and unique provider identity, allowing
additional authorized sources without changing the report/UI. Existing Google RSS
and GDELT adapters are supplied, with caches isolated by provider, CIK, company,
window, limit and rights reference. Tests use offline fixtures only.

Official access references checked during implementation:
https://www.sec.gov/search-filings/edgar-application-programming-interfaces
https://www.sec.gov/about/webmaster-frequently-asked-questions
https://gdeltproject.org/data.html

## Validation

- Ruff: passed across app, tests, dashboard, QA and configured scripts.
- Full pytest suite: **2,065 passed**, 208 dependency/deprecation warnings.
- Independent numerical/API checks: 500 numerical cases passed; health 200,
  guarded legacy market route 403, invalid numerical input 422.
- Dependency consistency (`pip check`): passed.
- Bandit on intelligence modules and the new UI: zero issues.
- Streamlit AppTest: search, selection, report rendering and changed-company
  report invalidation passed without external requests.
- Real Chrome: isolated offline report at 1440 and 390 pixels passed, including
  headline display and coverage tab, with no horizontal document overflow.
  Screenshots here use explicitly illustrative QA news, not live headlines.
- Existing full browser regression: **failed** on the absent Stock Explorer
  `Research view` selector. That script expects tabs and a shared notebook removed
  by the pre-existing feature branch's open-layout redesign. No assertion was
  bypassed and no production UI was rewritten to conceal this baseline mismatch.
- Git diff whitespace check: passed.

## Limitations / outstanding review

This is a draft integration, not a production release. Existing browser acceptance
must be updated to the current Stock Explorer product contract before release.
Live SEC/news calls were not validated in this run. GDELT remains optional after
previous HTTP 429 results. Provider permissions and deployment approval remain
operator responsibilities. There was no merge or deployment.

SEC coverage is filing entities and ticker records, not verified exchange listings
or complete global coverage. Only recent submissions are searched, not archived
filing pages. Same-day filing timing and event causation are unverified. No earnings
calendar, issuer-confirmed earnings-date extraction or historical earnings scenario
model is implemented. No forecast or factual-verification score is inferred.
Conservative exact legal-name matching can miss common shortened names; reviewed
alias metadata is supported by the earlier pipeline but not auto-invented in the new
report. No real-world precision/recall benchmark has been established. Coverage
counts are diagnostic counts, not a measure of completeness or accuracy.

Caches are process-local and reset on restart. SEC fair-access limits apply across
all workers/IP traffic; centralized rate budgeting is needed before multi-worker
scale. No Docker build, dependency vulnerability audit or full hosted deployment
check was performed in this run.
