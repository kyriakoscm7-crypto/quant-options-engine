# End-to-end engineering risk audit — November 3, 2026

Scope: draft PR #6, `safety/legal-risk-reduction-2026-11`. No merge or deployment authorized. This is an engineering assessment, not a legal opinion, provider permission, professional certification or prediction of litigation risk.

## Findings and fixes

| Area | Evidence and disposition |
| --- | --- |
| Public data routes | Main router, direct Discovery and standalone public research renderers use fictional simulations; Stock Explorer uses the official TradingView widget. Legacy Yahoo HTTP route always returns 403. Existing HTTP tripwire tests cover all 13 routes. Retained development engines are not approved public feeds. |
| Bundled data rights | Found an additional SQLite deployment snapshot with 359 company records (including prices/capitalizations) and 711 cached rankings. Removed it and ignored future discovery snapshots. Regression now rejects DB/CSV deployment artifacts. Previous Git history/publication remains; no retroactive rights clearance is claimed. Benchmark CSVs are software timing results, not quote feeds. |
| Privacy | No accounts, payments, uploads, brokerage connections or persistent visitor portfolio database in the public routes. Streamlit widgets transmit values to the server; synthetic market caches are global but contain no visitor holdings. Static Learn HTML calculates locally. Optional TradingView runs in the browser, after a session choice. Added the same connection explanation beside the settings toggle; clarified invented inputs and disconnected-session/log limits in Privacy. |
| API error reflection | Rejected inputs, validator contexts and model-level dictionaries were echoed in 422 responses. Removed values and contexts; redact unexpected field names too. Regression includes confidential markers as both keys and values. |
| Numerical errors | Extreme finite inputs could overflow scalar arithmetic or produce non-JSON numbers in vectorized outputs. Return a generic 422 for arithmetic/domain/JSON numerical failures, rather than a traceback or successful invalid result. Valid calculations retain existing values and Greek units. This is not a guarantee of every model's accuracy. |
| Resource exhaustion | Added a 4 MiB actual-body limit before JSON parsing, including chunked requests; 80-character scenario names; 10,000 combined scenario-position limit. Individual 10,000-option batch support remains. This bounds one request, not concurrent abuse. |
| Response privacy | API responses include `Cache-Control: no-store`, `nosniff`, and a no-referrer policy. No request-body logging added. These headers do not control host logs, client copies or upstream caches that disregard them. |
| Calculator UX | Added reasonable price/rate/dividend input bounds to Options/Greeks and price bounds to Scenario Explorer. Concise European-model/fees/assignment assumptions sit beside the inputs. Preserve all normal controls, outputs, charts and navy/pink styling. |
| Dependency security | Local audit found GHSA-xmj3-9gf7-h52w in setuptools 84.0.0. Require >=84.1.0 for installs/Docker and CI; patched local audit then passed. This is a point-in-time known-vulnerability check, not proof of complete security. |
| Container/CI | Container runs as UID/GID 10001 instead of root. CI also lints the public safety/widget/policy/simulation and options/Greeks modules. Existing full test, dependency audit and Docker health jobs remain required. |
| Claims and appearance | Real-stock widgets remain separate from synthetic models, with attribution/delay notices. No backend TradingView feed, broker execution or performance certification added. No wholesale visual redesign. Existing synthetic banners and compact policy menu remain. |

## Hosting: verified versus unknown

Read-only inspection of `https://quant-intelligence-km.streamlit.app/` on November 3 showed a running Streamlit interface with the earlier homepage and no draft Legal/Settings menu in the sidebar. Do not treat this branch's controls as live protection. No production settings were changed and no sensitive values were submitted. The public page cannot reveal the actual deployed commit, admin configuration, secrets, log retention, subprocessors or provider contracts; those remain operator checks.

[Current Community Cloud terms](https://streamlit.io/terms-of-use) restrict processing financial information and other sensitive personal information, and constrain commercial processing of personally identifiable information. The breadth of “financial information” needs host clarification for this project; fictional input guidance is a reduction measure, not a finding that hosting is permitted. Resolve this with Snowflake/Streamlit or choose suitable hosting before release. Confirm the deployer's eligibility, including the service's age requirement. Do not infer eligibility from possession of a GitHub account.

[Community Cloud status documentation](https://docs.streamlit.io/deploy/streamlit-community-cloud/status) describes host telemetry overrides and US hosting. Repository opt-out settings cannot promise zero host analytics. [Security documentation](https://docs.streamlit.io/deploy/streamlit-community-cloud/get-started/trust-and-security) describes shared responsibility and GitHub-derived administration permissions. Confirm admin MFA, collaborator access, logging/retention, backups and deletion practices in the actual account. Never put real income, debts, holdings, credentials or identifiers into hosted examples.

## Provider and content boundaries

[TradingView widget docs](https://www.tradingview.com/widget-docs/getting-started/) support its provided embedding mechanism. [Its terms](https://www.tradingview.com/policies/) restrict non-display processing and commercial use absent appropriate permission. Obtain clarification for any ambiguity about this site's audience/business use; the widget is not a backend data licence. Keep branding intact and do not obscure it with CSS. Confirm actual mobile rendering, exchange coverage and quote delays on the approved host. [Data FAQ](https://www.tradingview.com/widget-docs/faq/data/) distinguishes widget availability and paid-plan entitlements. See the detailed provider review in this folder.

[yfinance's documentation](https://ranaroussi.github.io/yfinance/) warns about personal-use restrictions and directs users to Yahoo terms. The linked Yahoo legal endpoint returned HTTP 999 during this review; its exact applicable regional terms have not been cleared. The safe public boundary does not rely on Yahoo permission. Google News RSS and SEC integrations remain development code only: separately review publisher rights, SEC fair-access rules, attribution, caching and public redistribution before exposing them. Public tests currently prevent their HTTP requests.

Inline SVG/HTML and mathematical charts were reviewed as local assets; the favicon's authorship/assignment and contributor rights have not been independently proven. Keep an asset provenance register before public promotion; open-source dependency licences do not grant rights in downloaded data or establish ownership of the app. No blanket licence of third-party material is asserted.

## Required external decisions

1. Canadian securities/technology counsel: assess actual business activities and audience, applicable registration/exemptions, marketing, Terms enforceability, mandatory consumer rights and privacy rules (including relevant provincial requirements). Review any financial interests/referral arrangements before adding them. [OSC guidance](https://oscinnovation.ca/education/securities) explains the business trigger; a disclaimer alone cannot determine status.
2. Privacy lead/operator: document purposes, lawful consent, access/deletion handling, retention, cross-border processors and actual session/log behavior. Confirm hosting suitability in writing. [OPC guidance](https://www.priv.gc.ca/en/privacy-topics/privacy-for-businesses/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/pipeda-compliance-help/guide_org/) is a starting point, not a determination that PIPEDA applies here.
3. Provider licensing: obtain explicit rights before backend real-market calculations, derived forecasts, exports or redistribution. Document exchanges, users, jurisdictions, caching, retention, attribution and termination. No retail subscription or environment flag substitutes for this.
4. Operator security: configure host-level request/concurrency/time/rate limits and HTTPS; verify secrets, least privilege and dependency patching. Confirm rollback, incident contact, monitoring and breach procedures. Consider professional liability/cyber coverage with an adviser; no policy is arranged here.

## Incident and request handling

Use the in-app private contact; public issues must not include confidential records. Triage reports, contain affected routes, preserve only necessary evidence with restricted access, rotate exposed credentials and contact host/provider as appropriate. Assess legally required notification and recordkeeping with qualified help; [OPC breach guidance](https://www.priv.gc.ca/en/privacy-topics/privacy-for-businesses/privacy-breaches-at-your-business/gd_pb_201810/) explains the federal framework where applicable. Do not promise deletion of host logs without verifying control over them. Reassess all these boundaries before adding analytics, monetization, accounts, uploads, persistence, AI advice or brokerage connectivity.

## Validation for this follow-up

- Python 3.11 full suite: **1,834 passed**, **86% app coverage**, 208 warnings (dependency/deprecation warnings and intentional extreme-number regression warnings).
- Ruff: app, tests, public safety/widget/policy/simulation and options/Greeks modules passed. `git diff --check` passed.
- Patched local environment: `pip-audit` reported no known vulnerabilities after upgrading setuptools to 84.2.1. Unpinned dependencies can change between installs; CI re-audits the resolved environment.
- Docker build succeeded. A non-root, read-only container with all Linux capabilities dropped and no-new-privileges enabled passed health, no-store headers, theoretical pricing and 403 market-feed checks. This tests packaging, not the production infrastructure.
- Local browser: official Apple widget loaded, with delayed-data indicator, provider logo and attribution visible. Initial off state and premium layout verified. Automated tests verify disabling/re-enabling and policy navigation. Intended production-host/mobile verification remains pending explicit deployment authorization.
- GitHub CI status must be checked on the final pushed commit; these local results do not imply remote CI or production success.
