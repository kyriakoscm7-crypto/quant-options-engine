# Earnings release validation — November 9, 2026

Release remains blocked. Keep PR #13 unmerged and `EARNINGSAPI_ENABLED=false`.

## Verified in this follow-up

- PR #13 base is `quant-intelligence-automation`; reviewed starting head
  `79825610dfc78cbc6728845d121cb90d73b983a5` was open/unmerged with four successful
  reported checks. New-head CI evidence is recorded on the PR after pushing.
- Authenticated Streamlit app listing targets that deployment branch and
  `dashboard/main.py`, Python 3.11. Saved secrets still select a Neon pooled
  endpoint and `neondb_owner`; enabled is false. No EarningsAPI key is present in
  that secrets document. Other runtime sources were not inspected. No settings,
  secrets, access rules or production database rows were changed.
- Authenticated EarningsAPI dashboard shows the Free plan. Its usage reset
  display is stale, so remaining quota was not inferred. No live API data
  endpoint was called and no provider quota was spent.
- [Official terms](https://www.earningsapi.com/terms), effective June 11, 2025,
  permit retrieval/display in one's own app or website and restrict republication
  of the proprietary feed. They do not explicitly authorize seven-day normalized
  PostgreSQL retention, public/private audience details, or longer backup/history
  retention. [Official docs](https://www.earningsapi.com/docs) list Free limits
  of 60/minute, 100/day and 1,000/month; the application's 250/month cap is separate.
- Submitted a written clarification via the authenticated
  [official support form](https://www.earningsapi.com/support). The visible
  confirmation said the request was submitted and a reply would go to the account
  email. Questions cover Free-plan public/private display, normalized shared
  caching up to seven days, inactive/expired records, Neon backups/history,
  attribution and paid licence requirements. No credentials were sent. A
  submission is not permission; a written provider response is still required.

## Changes and local evidence

- Live integration tests now require an operator-provisioned database comment
  matching `EARNINGS_TEST_DATABASE_MARKER`, checked read-only on every configured
  endpoint before writes. Both ledgers must be empty. The test never resets them.
  An optional pooled test URL alternates concurrent callers across endpoints.
  The marker is an operator attestation, not independent proof of Neon branch
  identity; verify project/branch identity before creating it.
- Added checks for snapshot reuse and failed-batch cooldown in fresh Python
  interpreters, with HTTP mocked/forbidden throughout. Credentials are not written
  to files or command arguments by the test. Child diagnostic output is suppressed
  because database error messages can contain credentials.
- Added a CI job with disposable PostgreSQL 16 and a restricted runtime role.
  The existing unit/security/browser and Docker gates remain.
- Full local suite: **2,252 passed, one live integration test skipped**, 223
  existing dependency warnings, Python 3.11.17 plus psycopg 3.2.10. Ruff and
  whitespace checks passed. Existing dependencies were reused locally; clean
  dependency validation remains a CI responsibility.
- Separate disposable local PostgreSQL 16: **all five provider tests passed**
  using a LOGIN role with CONNECT/USAGE/SELECT/INSERT/UPDATE, no CREATE on public
  and no DELETE on the budget table. Sixteen callers generated exactly seven
  mocked requests. New processes reused seven saved events. A later mocked 503
  charged another seven reservations; new processes respected its cooldown.
- Restarted only this disposable local database. PostgreSQL startup changed
  from `2026-11-09 19:10:29.202536+00` to
  `2026-11-09 19:13:09.987468+00`. Fresh application connections reused the first
  test database's seven-event snapshot/calls=7 and the second database's
  failed-refresh cooldown/calls=14 without HTTP. No ledger resets were used.

## Unresolved release gates

1. Neon is authenticated in the browser, but its dedicated connector was not
   installed in this chat at validation time. Installation was requested. No
   browser-held production credential export or alternative credential-copy
   workaround was attempted. Actual psycopg direct/pooler tests, cross-endpoint
   concurrency and isolated Neon restart/process persistence remain unverified
   in this follow-up. Local PostgreSQL tests are not substitutes for those gates.
2. The existing role remains `neondb_owner`. The earlier PR evidence reports
   sufficient privileges but excess CREATE/DELETE rights. No new Neon runtime
   credential/role was created and no production URL was changed. Provision and
   validate a restricted runtime role through an approved secure workflow.
3. Actual Streamlit redeployment/restart persistence is unverified. No production
   restart was performed. Validate using an isolated staging deployment/branch.
4. Obtain written provider permission for the intended display and retention.
   The seven-day cache TTL limits serving, not physical retention. If the answer
   requires hard deletion, implement/test retention and backup handling before
   enabling the integration. Account history access is not a caching licence.
5. Configure the provider key securely only after rights and database validation;
   its absence from saved Streamlit secrets is not proof no other source exists.
