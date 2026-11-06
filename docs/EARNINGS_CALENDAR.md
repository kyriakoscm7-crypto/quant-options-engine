> Current public calendar: independently researched issuer-announced schedule facts are shown in-app. See [issuer calendar](ISSUER_CALENDAR.md). Finnhub setup below remains disabled.

> Superseded November 6, 2026: the public portfolio branch disables Finnhub unconditionally. The setup below is historical and cannot enable this build. No live calendar or replacement event feed is provided. See [public review](PUBLIC_POLISH_2026_11_06.md).

# Earnings calendar — local Mac setup

Reviewed November 6, 2026. Adapter: Finnhub official `/api/v1/calendar/earnings`, US only (`international=false`). No website scraping, proxying, sample credentials or inferred SEC earnings dates.

## Provider decision and authorized scope

Finnhub's [pricing](https://finnhub.io/pricing) lists $0/month, 60 requests/minute, US earnings calendar, one month of historical data and new updates. [API documentation](https://finnhub.io/docs/api/earnings-calendar) specifies date, symbol, reporting session and non-GAAP actuals/estimates. Account entitlement and upcoming coverage must still be tested with your own key. Earlier weeks may be outside your plan; a successful empty result never proves that nobody reports.

[Terms](https://finnhub.io/terms-of-service), especially Redistribution Rights and Personal Use: personal plans allow your own non-business use; sharing access to data or derived results requires written approval. Select `personal_local` only for your own local research. A private demo shown to other people, family/shared access, company use or the public Streamlit site requires written approval. Do not add these secrets to that site under personal terms. For a shared demo, obtain a written Finnhub agreement covering display, derived use, US calendar, audience and in-memory 15-minute caching, then select `written_agreement`. This setting records operator scope; it is not proof of a legal grant. Subscription termination requires deletion; stop/restart the app and remove the key/scope to discard memory caches.

FMP was considered: [pricing](https://site.financialmodelingprep.com/developer/docs/pricing) shows Basic $0 with limited symbols/history, Starter $19/month billed annually (US) and Premium $49/month billed annually (US/UK/Canada). Its [FAQ](https://site.financialmodelingprep.com/faqs?code=calendar) also calls the calendar paid, so free upcoming entitlement is uncertain. Its pricing explicitly requires a separate Data Display and Licensing Agreement for display/redistribution. Its “earnings confirmed” endpoint is retrospective, not proof that future dates are confirmed. Finnhub is the lower-cost documented local option. No paid purchase or registration was made by this change.

## Configure on your Mac

1. Register yourself at https://finnhub.io/register and review the terms. Get your API key from https://finnhub.io/dashboard. Do not paste it into chat, screenshots, a notebook or a tracked file.
2. In Terminal:

   ```sh
   cd '/Users/Kyriakos/Documents/ChatGPT/Quant Intellegence App/repo'
   cp -n .streamlit/secrets.example.toml .streamlit/secrets.toml
   chmod 600 .streamlit/secrets.toml
   open -e .streamlit/secrets.toml
   ```

3. In that local editor only, fill `api_key` inside `[earnings]`. Leave `use = "personal_local"` only for your own local non-business research. Save. The file is ignored by Git. No real key is bundled. Environment alternatives: `FINNHUB_API_KEY` and `QI_EARNINGS_USE` override the respective file fields. `.env` files are not automatically loaded.
4. SEC company research separately needs `QI_SEC_USER_AGENT` containing your genuine operator contact, following the existing Discover setup. Calendar access itself does not require SEC access.
5. Start from the repository directory:

   ```sh
   .venv/bin/python scripts/check_earnings_calendar.py
   .venv/bin/python -m streamlit run dashboard/main.py --server.address 127.0.0.1
   ```

6. Open Discover → Earnings this week. Check the retrieved timestamp, current week and next week, then open a ticker's research card. A key/access error means it is not live yet. Do not describe the feed as live until the local check succeeds with actual events. The checker does not print keys or event data. It reports empty responses separately.

## Data semantics and reliability

Weeks are Monday–Sunday using `America/Toronto` and calendar arithmetic across DST/year boundaries. Finnhub supplies date-only values and bmo/amc/dmh market-session labels, not precise instants or an event timezone. We retain that calendar date without converting a fictitious UTC midnight. Exact times and source timezone remain unavailable; retrieval instants are stored aware UTC and displayed Toronto-local.

This provider does **not** expose a documented company-confirmation flag or event update timestamp. All dates are labeled unconfirmed (estimated versus confirmed unknown), including records with actual EPS. Retrieval time is not represented as source update time. The UI never calls these company-confirmed dates; primary issuer verification would require a separate authorized source and evidence. Calendar data is not used in financial scores, notebooks or exports.

Normalize strict dates/tickers, reject invalid rows, deduplicate exact events and withhold issuers with conflicting dates in one week. Report rejected counts and incomplete coverage. Keep provider symbols unchanged; clicking a card resolves identity through the existing SEC directory/deep-dive, with no fuzzy substitution or fabricated research. Missing SEC setup or unsupported identity yields a visible warning.

Requests use HTTPS, fixed host, header authentication, ten-second timeout, no redirects and up to three attempts for network/429/5xx failures. Retry-After numeric delays are respected up to five seconds; longer waits fail visibly. Success cache: 15 minutes; error cache: 30 seconds; max 64 entries; keyed by credential digest, scope and date range. Shared process lock coalesces reruns. Expired data is never served; no stale fallback or disk persistence. Error text never includes provider payloads, request URLs or credentials. Restart clears caches, including on credential revocation.

## Verification boundary

Automated contract/UI tests use explicitly synthetic TEST events and mocked HTTP responses, not live issuer verification. Real browser checks on the actual app cover the no-key setup path, navigation and responsive display. A real authenticated response remains dependent on local registration/key setup; an unauthenticated request cannot establish live entitlement.
