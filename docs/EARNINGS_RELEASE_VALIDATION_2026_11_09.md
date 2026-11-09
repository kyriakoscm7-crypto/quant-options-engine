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
  secrets or production ledger rows were changed. The approved role provisioning
  described below changes database privileges only.
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
- A subsequent documentation-head CI run exposed an existing browser test
  synchronization race: the Explorer export's thesis was empty. Both routes
  expose the same notebook field labels, so the test could type into Discovery
  before the Explorer rerender arrived. The test now waits for the Explorer-only
  Company overview heading before editing. Immediate form submission and the
  exact exported-text assertion remain unchanged; no product behavior or
  acceptance condition was relaxed. Repeated fresh Chromium-session verification
  and latest-head CI outcomes are recorded on the PR.
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

## Completed after Neon connector installation

- Verified existing project `young-surf-61669228` / `quant-options-engine` in
  organization `org-round-dew-16819540`. Production/main branch is
  `br-withered-snow-bdyhly48`. Read-only production checks confirmed both earnings
  tables remain empty and the deployed `neondb_owner` has the required table
  privileges, plus excess CREATE/DELETE permissions.
- Created child branch `br-aged-morning-bdoi29kq`, named
  `pr13-driver-validation-20261109`, with compute `ep-flat-union-bdspru6n`.
  All synthetic test writes and compute restart occurred on this child only.
  The branch is retained for evidence; it was not reset or deleted.
- Created a branch-local `qi_earnings_runtime_test` role: CONNECT/USAGE and
  SELECT/INSERT/UPDATE on the two earnings tables. CREATE/DELETE/TRUNCATE,
  superuser, database/role creation, replication and RLS bypass are unavailable.
  Automatic future-table SELECT grants were removed.
- Real psycopg 3.2.10 direct and `-pooler` connections passed **all five provider
  tests** with mixed concurrent callers and fresh interpreter reuse. Sixteen
  callers shared exactly seven mocked requests; a simulated failed batch's
  charge/cooldown survived new processes. No real provider calls occurred.
- Verified pooler behavior separately: four simultaneously open direct clients
  had four distinct backend PIDs (1582–1585), while four open pooled clients
  reused backend PID 1262 across committed queries.
- Both client connections used TLS with `sslmode=verify-full`, the trusted
  certifi CA bundle, and `channel_binding=require`. The local libpq system CA
  lookup initially failed verification; selecting certifi fixed the trust store
  without weakening verification. Credentials were generated for the isolated
  test role and passed in process memory/environment only. No production
  password was exported, displayed or written to temporary files.
- Seeded one additional synthetic reporting week through the application service
  (seven mocked requests), then restarted only the test compute. PostgreSQL
  startup changed from `2026-11-09 19:21:17.314621+00` to
  `2026-11-09 19:26:06.206583+00`. Fresh direct and pooled app connections read
  seven saved events with identical payload MD5
  `c627225eee1a0d7d2ba036abc6fe1c5e`, calls=21 and the prior failed-week cooldown
  `1794934800`. **Zero HTTP requests** occurred after restart. These are synthetic
  reservations only; no production ledger rows were inserted/updated/reset.
- Created production `qi_earnings_runtime` with a provider-generated credential
  retained by Neon. After explicit user approval, granted INSERT/UPDATE only on
  the two earnings tables and removed automatic future-table SELECT grants.
  Read-only login as that role succeeded; verified CONNECT/USAGE and table
  SELECT/INSERT/UPDATE, no CREATE/DELETE/TRUNCATE, no privileged role attributes,
  and no membership in `neon_superuser`. Both production ledgers remain empty.
  Streamlit initially still used the original owner role; the subsequent secure
  user handoff below completed the saved configuration change.

## Final secure configuration handoff

- The owner refreshed the main-branch owner and runtime credentials through
  Neon's secure UI, then updated only the three existing Streamlit connection
  values. The assistant did not enter, export or display production passwords.
  Role metadata confirms owner refresh at `2026-11-09 19:37:49 UTC` and runtime
  refresh at `2026-11-09 19:43:37 UTC`. The two isolated branches' inherited
  owner credentials were also refreshed with explicit user approval; generated
  values stayed inside Neon and were suppressed from outputs.
- Reopened saved Streamlit secrets read-only and verified these non-secret
  mappings on the main endpoint: `DATABASE_URL` = owner/pooled,
  `DATABASE_URL_UNPOOLED` = owner/direct, `EARNINGSAPI_DATABASE_URL` =
  `qi_earnings_runtime`/pooled. Each URL requires TLS and channel binding.
  `EARNINGSAPI_ENABLED=false`; no provider key appears in that saved document.
  The user reported preserving all other secret values; their original contents
  were not exported for comparison.
- A fresh read-only main-branch login as `qi_earnings_runtime` succeeded after
  refresh; both production earnings tables remained empty. The actual Streamlit
  application loaded its dashboard normally following the secret updates.
  Saved mappings and general app health do not prove the disabled/unmerged
  earnings path has opened a production database connection.

## Unresolved release gates

1. The new role is now selected in saved Streamlit secrets. Validate the actual
   earnings path in an isolated Streamlit staging deployment before activation.
   Real Neon compute restarts and fresh Python application processes passed;
   end-to-end hosted earnings snapshot persistence remains unverified while
   PR #13 is unmerged and the feature is disabled. The general dashboard health
   check following the secret updates is not a substitute for that test.
2. Obtain written provider permission for the intended display and retention.
   The seven-day cache TTL limits serving, not physical retention. If the answer
   requires hard deletion, implement/test retention and backup handling before
   enabling the integration. Account history access is not a caching licence.
   The official [backfill/sync example](https://www.earningsapi.com/docs/examples/calendar-backfill-sync)
   recommends storing calendar responses, supporting database use in principle,
   but gives no specific retention/backup or audience licence conditions.
3. Configure the provider key securely only after rights and database validation;
   its absence from saved Streamlit secrets is not proof no other source exists.
