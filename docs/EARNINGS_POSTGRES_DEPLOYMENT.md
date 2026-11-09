# Production PostgreSQL earnings ledger (opt-in only)

The hosted EarningsAPI calendar is **disabled by default**. Do not flip
`EARNINGSAPI_ENABLED` until the following is verified.

## Why PostgreSQL

Streamlit Community Cloud does not guarantee persistent local disks. The
SQLite budget and snapshot ledger is safe only on one host with a durable
shared filesystem. The PostgreSQL implementation uses a single central
transactional ledger; every application replica must use that same database.

## Provision an isolated private database

1. Provision an encrypted, managed PostgreSQL instance with backups and
   durable storage. Verify provider pricing and avoid public database access
   where practical; grant the Streamlit app only the minimum permissions.
2. Connect using a TLS-enforcing PostgreSQL URL and apply
   `db/earnings_postgres.sql` **once** via an operator/admin account.
3. The app role needs SELECT/INSERT/UPDATE on `earnings_budget` and
   `earnings_weeks`. It does not need DELETE, DROP or CREATE.
4. Confirm records survive a database restart and an app redeployment.
5. Run the isolated integration test with `EARNINGS_TEST_DATABASE_URL`
   pointing to a disposable database that already has the schema.
   This test **deletes both earnings tables' test contents**, so never use
   production credentials.
6. Check the provider's plan, display/caching permissions and quota. All
   other applications using the same key are outside the app's 250-request
   ledger.

## Server-only Streamlit secrets

Use Streamlit Cloud **App settings → Secrets**, not GitHub code, to set:

```toml
EARNINGSAPI_API_KEY = "your-private-key"
EARNINGSAPI_DATABASE_URL = "postgresql://app_user:password@your-host:5432/earnings?sslmode=require"
EARNINGSAPI_ENABLED = false
```

The URL above is a **placeholder**. URL-encode reserved characters in the
password. Prefer stricter server-certificate validation where supported.
Never share the connection string in chat, screenshots, source files or logs.

After schema, isolated tests, database persistence and key entitlement are
confirmed, change only `EARNINGSAPI_ENABLED = true`, then restart the app.
Test the weekly calendar once. Check that a second visit spends no additional
provider requests, and that a restarted app reads the same snapshot.

If `EARNINGSAPI_DATABASE_URL` is configured, the app selects PostgreSQL.
Otherwise, the existing `EARNINGSAPI_CACHE_PATH` SQLite path remains for
single-host development. Do not configure a temporary cloud SQLite file as a
production substitute. A configured PostgreSQL failure must fall back to
issuer announcements without making untracked provider calls.

## Operational guarantees and limitations

- The shared month budget row is locked transactionally before checking
  the week. Every fetch reserves **seven requests** and a **24-hour retry
  cooldown**, committed before any external HTTP call.
- The monthly app ledger caps at **250 reserved requests**. A failed batch,
  crash or process termination still consumes its reservation.
- Weekly snapshots expire after seven days or the Friday reporting-week
  rollover, whichever comes first.
- A database outage fails closed, and the limited issuer calendar remains
  accessible. No automatic deletion of historical budget rows occurs.
- This is not a provider-account-wide budget when separate clients use the
  same API key. App replicas must all point to the *same* database.
- Provider dates are not all issuer-verified. Keep the existing disclosure
  and official-announcement reconciliation.
- No external storage is provisioned by this PR; no credentials are stored
  in the repository; no API activation or production deployment is included.

## Rollback

Set `EARNINGSAPI_ENABLED = false` before changing connection settings.
The curated fallback is independent of the PostgreSQL service. Do **not**
delete the monthly ledger to troubleshoot a failed API request.
