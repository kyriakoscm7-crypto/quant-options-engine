# External review register — November 4, 2026

Owner: Kyriakos Margaritis. Intended audience: owner and cousin Michael only.
Status: inquiries prepared below; **not sent, no provider response or legal clearance obtained**.
No account, Sharing, repository visibility, secret or production setting was changed.

## H03 — hosting suitability: unresolved external blocker

Use public-company observations, source links and invented calculator/portfolio inputs only.
Do not enter actual income, debts, savings, holdings, accounts, brokerage statements,
identity records, passwords or other protected personal financial information.
Private access reduces audience; it does not establish hosting eligibility or a licence.

Primary source reviewed: [Streamlit terms and Community Cloud addendum](https://streamlit.io/terms-of-use).
The operative addendum, rather than its summary, must be applied to the actual use.
Code cannot certify a contract interpretation or the host's retention/deletion behavior.

Prepared inquiry for the host's official support channel:

> We operate an invitation-only educational research prototype for two people.
> It displays official third-party browser widgets, stores public-company notes
> in Streamlit session state and accepts fictional option/portfolio inputs.
> It has no brokerage integration, transactions, paid advice or real account records.
> Please confirm whether this precise use is eligible under the operative Community
> Cloud agreement, especially its protected-information restrictions. What are the
> hosting region, session and log retention, deletion process, subprocessors,
> telemetry overrides and access-revocation semantics? If this use is ineligible,
> which hosting product/contract is appropriate? We will not introduce sensitive
> records, commercial use or more users before a written determination.

Acceptance evidence: written response/contract version, date, reviewer and approved data classes.
Until obtained: no suitability claim, no sensitive/commercial expansion. If declined,
prepare a separately authorized migration with equivalent authentication and privacy controls.

## TradingView operator permissions and L04 — unresolved external review

Official widgets remain browser display only. No backend scraping, message extraction,
redistribution, widget-value calibration, or ingestion into mathematical models.
The chart copyright now follows the same official copyright markup as the detail
widgets, without the app's 12px attribution rule or anchor-color override.
That correction is not a provider certification.

Primary sources reviewed: [widget general FAQ](https://www.tradingview.com/widget-docs/faq/general/),
[data FAQ](https://www.tradingview.com/widget-docs/faq/data/),
[terms](https://www.tradingview.com/policies/).

Prepared inquiry for the provider's official widget support channel:

> Can our two-viewer, private, noncommercial educational website embed your official
> advanced chart, screener, symbol info, financials, profile, technical-analysis and
> timeline widgets using the documented configuration options and unmodified copyright
> markup? We render one selected Stock Explorer panel at a time after session consent.
> We do not access widget data outside its display or use it in models/exports.
> Please confirm operator, exchange, audience, branding and attribution requirements
> for this use, including whether any separate written permissions are required.

Acceptance evidence: written determination covering actual domain, widgets, both viewers,
markets, operator rights and branding. A personal subscription is not assumed sufficient.
Yahoo routes remain unreachable; the deprecated market API stays 403. Future feeds
require specific rights for both viewers, server analytics, derived outputs, caching
and exports; no flag may enable them as a substitute for review.

## H04 — actual API host: unverified

Only localhost API evidence was supplied by the audit. No verified public API origin,
TLS/proxy configuration, deployment ID or provider logs have been identified.
Local/container tests establish code behavior, not the protection of any external host.

Required operator evidence before publishing a separate API:

- Identify the actual host/origin, deployment SHA and proxy; record whether no API is deployed.
- Production startup must reject absent/short tokens. Store a random token in the host secret store;
  never browser code or repository. Test unauthenticated 401, valid calculation 200,
  authenticated legacy market 403, over-budget 429, body limit 413 and concurrency denial.
- Configure TLS, trusted proxy addresses, aggregate rate/concurrency limits across workers,
  body-read deadline and hard upstream execution timeout. App-level budgets are per process.
- Health exposes no secret or calculation data. Do not treat Streamlit sign-in as API auth.
- No public-host probing, configuration or secret changes are authorized by this fix branch.

## Operational privacy and incident procedure

Vendor inventory: Streamlit/Snowflake hosting and authentication; GitHub source/CI;
TradingView opted-in browser panels; SEC/external sources opened by user links.
Notebook exports are user-created local copies, outside app deletion controls.
No app database persistence was added. Session-only does not promise immediate destruction
of disconnected session memory, host logs, browser caches or external provider logs.

Owner procedure: review audience/collaborators and MFA, test a signed-out account and
revoked viewer in independent sessions, record host retention/deletion contacts, and
review permissions before changing audience or data classes. For suspected exposure,
restrict the affected service through the host, preserve minimal non-sensitive evidence,
revoke/rotate affected credentials, contact relevant vendors and obtain professional
notification advice. Do not paste credentials or private records into issues/logs.

No legal immunity, adviser-registration exemption, regulatory approval or provider
endorsement is asserted. Reassess jurisdiction, compensation, promotion and conduct
before expanding beyond the restricted educational prototype.
