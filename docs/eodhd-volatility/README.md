# EODHD owner-only historical volatility (pre-release)

This integration is **disabled by default**. It is for a single authenticated,
nonprofessional owner only. EODHD's personal-use conditions do not permit
showing the feed **or derived results** to cousins, collaborators, employers,
or a public preview. Changing the app to shared/public requires an appropriate
commercial license before activation.

## Setup in a controlled release

1. Create a personal EODHD account and check the current personal-use rules.
   The Free plan currently advertises **20 calls per UTC day**, at most
   **one year of EOD history**. The adapter reserves at most 18/day to
   leave a buffer. Calls reset at midnight UTC.
2. Keep the website's existing authenticated owner-only access. The runtime
   checks `st.user.is_logged_in` AND exact email match against
   `EODHD_OWNER_EMAIL`; it fails closed if Streamlit does not expose an
   authenticated identity. An IP address, query parameter, or private URL
   is **not** sufficient proof of identity.
3. Apply `db/eodhd_volatility.sql` through a controlled migration in the
   existing Neon project. **Do not reset, alter or reuse earnings ledgers.**
   Grant only SELECT, INSERT and UPDATE on `eodhd_daily_budget` and
   `eodhd_prices_cache` to the restricted runtime role. Never test with
   real provider quota or mutation against the production earnings ledger.
4. In **Streamlit server secrets**, without replacing any existing values,
   add the following keys (fill actual values only in the secret manager):

   ```toml
   EODHD_ENABLED = false
   EODHD_OWNER_EMAIL = "YOUR_SIGNED_IN_EMAIL"
   EODHD_API_KEY = "YOUR_PERSONAL_EODHD_TOKEN"
   EODHD_DATABASE_URL = "YOUR_EXISTING_NEON_POOLED_CONNECTION_STRING"
   ```

   The provider token is never accepted from the UI, logged, or committed.
5. Run isolated database tests with a **separate Neon test branch/database**,
   mock HTTP responses and an explicit test marker. Verify the real
   Streamlit authentication identity, correct provider entitlement and
   the complete server-side authorization gate before activation.
6. Only then set `EODHD_ENABLED = true`. Check a ticker on the owner's
   session, and verify the derived data is absent in a signed-out session
   and any collaborator account. Restore `false` immediately on an access
   regression.

## Data semantics

- EODHD `adjusted_close` adjusts for **splits and dividends**. Daily
  log returns are computed on adjusted closes, then 20- or 60-observation
  rolling sample standard deviation is annualized with `sqrt(252)`.
- This is historical/realized volatility, **not** implied volatility or
  a forecast. Results can change when EODHD revises adjusted history.
- One full series is refetched on a 24-hour policy instead of appending
  just the latest price because corporate-action adjustments can rescale
  the entire adjusted history.
- A cache hit consumes zero EODHD calls. On a cache miss, the budget
  reservation is **committed before the request**. Failed requests still
  count; there is a one-hour retry cooldown. Missing DB/schema or exhausted
  budget fails closed, never silently makes an untracked HTTP request.
- Provider-specific tables are isolated from EarningsAPI. Stored data is
  retained only for personal use; no downloadable provider dataset or
  public derived volatility chart is exposed.

Official provider references:
- https://eodhd.com/help/personal-use
- https://eodhd.com/help/storage
- https://eodhd.com/help/ai-tools
- https://eodhd.com/help/plans
- https://eodhd.com/financial-apis/api-for-historical-data-and-volumes
