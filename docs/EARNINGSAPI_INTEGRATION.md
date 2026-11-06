# EarningsAPI.com integration (public portfolio build)

Provider: [EarningsAPI.com](https://www.earningsapi.com/) using the documented
[GET /v2/calendar/earnings](https://www.earningsapi.com/docs/calendar-earnings)
endpoint, one request for each day of a Monday–Sunday week.

## Configure the key

Sign up for a provider account. Copy the API key into the **server environment**
as `EARNINGSAPI_API_KEY`, or into your **untracked** local
`.streamlit/secrets.toml`:

```toml
EARNINGSAPI_API_KEY = "paste-your-own-key-here"
```

Do not put it in the repository, browser code, app text, screenshots or chat.
The existing `QI_SEC_USER_AGENT` server environment setting is separately
required for SEC company analysis; the Earnings calendar itself needs only the
EarningsAPI key. Restart Streamlit after adding the secret.

For Streamlit Community Cloud, configure the key in the app's private Secrets
management UI, not in GitHub. Only do so once the account's display terms and
plan are suitable for the visitors who will use your deployment.

## What the public page does

With the key configured, Discover → Earnings calendar reads a week from the
provider and displays company name, ticker, reporting date, and the provider's
before/after/unspecified market-session group. Click **Research** on a company
to open **Research → Stock Explorer** with its ticker preselected when the
existing verified search can identify an unambiguous exchange listing. If the
listing cannot be resolved, the research page requests an exact listing rather
than guessing. The SEC-based Find stocks page remains separate.

Without a key, or when a provider request fails, an independently curated
small set of issuer-announced events remains available with links to original
announcements. No events or estimates are invented.

## Reliability and permissions

- Provider events are **not automatically company-confirmed**. An earnings
  release can shift; check the original company investor-relations page before
  relying on a date. `pre` and `after` are market-session categories, not
  precise local timestamps.
- Dates are kept exactly as reported, with a Monday–Sunday Toronto calendar
  view and no fictitious timezone conversion.
- Only displayable event fields are normalized. Missing estimates remain
  missing. We do not calculate investment scores from this feed.
- Fetches use HTTPS and a fixed provider endpoint, 12-second timeouts, and
  reject HTTP errors. A partially failed week is withheld, never displayed as
  a complete calendar.
- Valid full-week responses are cached **in server memory for six hours**.
  Seven daily requests are needed per uncached week. No raw data is saved to
  disk or redistributed as a separate feed.
- The server-side API key is never rendered; internal errors do not include
  request URLs, response bodies or secrets.
- Published provider terms explicitly allow displaying earnings content in
  your own website, but prohibit republishing its proprietary data feed.
  See [Terms](https://www.earningsapi.com/terms). Re-check plan entitlements
  and terms before publishing or extending to derived datasets.

## Verification

Offline contract tests in `tests/test_earnings_api_provider.py` use **synthetic**
payloads and mock HTTP responses. They do not verify an authenticated live
response or company-confirmed dates. After adding your own key, start:

```sh
python -m streamlit run dashboard/main.py --server.address 127.0.0.1 --server.port 18520
```

Open Discover → Earnings calendar and confirm the page shows a retrieved
timestamp and the expected weekday entries. Click **Research** and confirm the
Stock Explorer selection. Do not consider the data live until an authenticated
request has succeeded.
