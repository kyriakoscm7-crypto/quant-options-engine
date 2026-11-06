# Simple Discover navigation

Discover has two real sidebar destinations, styled by the existing sidebar:
**Find stocks** (the existing stable Discover route) and **Earnings this week**.
There are no Discover page-selection tabs. The legacy Market Scanner alias still
resolves to Find stocks. Stock Explorer, consent boundaries and the local research
notebook are retained.

## What works

Find stocks preserves the SEC gateway, official identity resolution, bounded scans,
multi-year factor engine, exclusions, formulas, score coverage rules, original-filing
cross-check and stress calculations. Candidate cards lead with observed sales and
operating-profit facts, a dated margin sparkline and one company-research action.
Missing evidence produces an unavailable synopsis, never replacement values.
Research options, comparisons and archetype choices are optional; the numerical
archetype fit is inside company detail and explicitly is not an investment rating.
History, calculations, scenarios and evidence checks are collapsed initially.

The default scan uses an editable editorial starting set, not a recommendation or
market-wide screen. NVIDIA, Meta, Microsoft and Apple use the same card renderer
and real SEC resolution; production contains no fixture issuer values.

## Source coverage and limits

- SEC annual USD US-GAAP issuer evidence: supported when the operator configures
  a genuine `QI_SEC_USER_AGENT` contact. Directory/facts caching and SEC pacing
  remain unchanged. This revision does not claim a fresh live SEC retrieval.
- Original annual filing checks: on demand; the same issuer origin as SEC JSON,
  not independent corroboration.
- Independent fundamentals, prices/valuation, market conditions, analyst opinions:
  not connected. No multi-source or investment-attractiveness composite is computed.
- Earnings: **no approved provider and no connected weekly adapter**. The page
  offers Toronto-local Monday–Sunday week navigation and a transparent unavailable
  state. This is not a zero-event calendar. No event grid or clickable event
  companies is enabled until verified data exists. Company research is available
  through Find stocks. No SEC filing date is presented as an earnings date.

## Safe earnings adapter integration

There is deliberately no environment switch that trusts an arbitrary endpoint,
JSON upload, credential or self-attested license. Do not scrape calendars or use a
provider API merely because a key is available. An integration needs a separately
reviewed implementation before the unavailable state can be replaced.

1. Review the provider's actual contract: dataset owner, users/geography, display,
   derived use, retention, caching, attribution and expiration. Record the approved
   grant in `app/intelligence/discover_evidence.py:APPROVED_SOURCES`. Its registry is
   intentionally empty today; adding a key does not register a provider.
2. Implement a server-side provider-specific weekly adapter with an interface such
   as `events(start: date, end: date) -> list[Evidence]`. The existing
   `LicensedProvider.evidence(cik)` is company-scoped and does **not** discover a
   market-wide calendar. Do not mistake a scan of six companies for a full calendar.
3. Restrict requests to the provider's reviewed HTTPS host, with no arbitrary user
   URLs, redirects or credentials in browser output. Bound timeout, response size,
   pagination, request frequency, cache TTL and retention. Read credentials from
   server environment or the existing secrets mechanism; never commit keys.
4. Resolve each event to the official SEC identity (ticker, CIK and issuer), retain
   the provider source URL, dataset owner, retrieval/as-of timestamps, confirmation
   state, event date, timezone and optional exact scheduled timestamp. Date-only
   records must stay date-only. Reject unknown identities, invalid timestamps,
   stale records and conflicting dates; deduplicate syndicated owners. Preserve
   revised/cancelled-event semantics and distinguish empty-success from feed failure.
5. Reuse `corroborate` for upcoming company evidence and inspect `confirmed` before
   displaying a confirmed event. Its current freshness gate rejects past dates;
   **do not use it unchanged for completed events earlier in the displayed week**.
   Historical week support needs a separate knowledge-time-aware validator and
   documented retention permission. Exact times convert to the viewer timezone;
   date-only records retain the source timezone.
6. Only render an event button after these gates. On click, resolve/load the verified
   company with `company_deep_dive`; surface provider/SEC failure without substitute
   facts. Reuse company research and preserve a return-to-week action. Do not infer
   earnings outcome, analyst sentiment or investment merit from an event date.
7. Test week/year/DST boundaries, date-only records, before/after-market times,
   revisions/cancellations, stale/conflicting/estimated events, unapproved/expired
   grants, identity mismatches, pagination, outages and successful empty weeks.
   Add server-side secret-leak checks and a licensed staging end-to-end check before
   enabling the provider. Extend the source grant schema for retention/geography
   if needed; the existing minimal grant alone does not establish all rights.

Until that work and a genuine approved credential exist, leave the current honest
unavailable state in place. There is no working earnings setup command today.

## Local Mac update

In the user's clone (`~/Projects/quant-options-engine`), first inspect local changes.
Commit or stash any personal work before switching branches; do not overwrite it.

```sh
cd ~/Projects/quant-options-engine
git status --short
git fetch origin
git switch feature/discover-intelligence-v2
git pull --ff-only origin feature/discover-intelligence-v2
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
# Keep/set QI_SEC_USER_AGENT to your genuine operator contact in this shell.
python -m streamlit run dashboard/main.py --server.address 127.0.0.1 --server.port 18520
```

Stop the previous foreground server with Ctrl-C before restarting on that port.
Open http://127.0.0.1:18520 and expand Discover. Earnings remains unavailable until
an approved integration exists. No merge or deployment is part of this revision.

## Verification

See the PR revision for the exact test results and commit. Screenshots in
`docs/images/discover-simple/synthetic-*` use prominently labeled offline QA facts,
not live issuer data. `calendar-*` and `sidebar-*` capture the actual app routing
with the unavailable feed. Browser scripts check responsive overflow, two sidebar
routes, weekly navigation, search/comparison, company drilldown/back, keyboard
scenario changes and source failure behavior. These are focused accessibility
checks, not an exhaustive screen-reader or device certification.
