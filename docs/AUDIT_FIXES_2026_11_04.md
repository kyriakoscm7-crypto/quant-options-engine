# Audit implementation checklist — November 4, 2026

Scope: Quant Intelligence, `kyriakoscm7-crypto/quant-options-engine`, never M20.
Fix branch: `fix/production-audit-2026-11-04`, forked from fetched production
`3611d515b22b87a323785320bfafa8ed41748a31`. Production and historical backups unchanged.
This is a review candidate, not an approved investment system or a deployed release.

The full attached report was read before edits. H01–H04, M01–M09, L01–L04 and
phases A–D form this checklist. Phase E is conditional future expansion, deliberately
not implemented without separately verified data/hosting rights.

## Finding-by-finding review

| ID | Code/evidence | Status and practical limit |
|---|---|---|
| H01 | `dashboard/strategy_research.py`; `test_h01_first_day_loss_and_initial_entry` | Fixed: initial 100 included in drawdown peak and chart; initial long exposure counted. Audit shock produces -50.074975% drawdown and one entry. Prior-close/next close-to-close simplified execution disclosed. |
| H02 | `dashboard/discovery_notebook.py`; real `qa/browser_acceptance.py`; `test_final_form_field_snapshot_and_v1_restore` | Save/prepare form atomically submits all fields. Immutable JSON bytes per saved session revision; button identifies revision and does not rerun on download. Browser checks exact final-field bytes, then a second Explorer edit/export. Users must save and wait for the displayed revision before downloading it; unsaved drafts are excluded explicitly. |
| H03 | `dashboard/legal_pages.py`; `EXTERNAL_REVIEW.md` | External blocker remains: host eligibility, retention and permitted data classes need written operator/host determination. Prepared inquiry is unsent. Fictional/public-company inputs only; no legal immunity or hosting clearance claimed. |
| H04 | `app/api/main.py`, `app/api/safety.py`, Docker and API regressions/smoke | Code fixed: production import/startup requires a >=32-character token; explicit development mode rejects remote clients. Per-process budget applies even without token; body bytes/time and concurrent requests bounded. Public API host/proxy/TLS/global throttling remains unverified and is a release gate. |
| M01 | `dashboard/premium_home.py`, `dashboard/main.py`; parameterized home-card regression; browser navigation | Portfolio mapping added; cards, network actions and shortcuts use session callbacks. Compatibility query URLs remain supported. Reload/new-tab/browser-history reconnections can create a new session; export before leaving. No claim of persistence across reconnects. |
| M02 | `dashboard/model_handoff.py`, Options/Greeks/Scenario; roundtrip and absent-widget regressions | One durable `qi_model` state; widget keys hydrate from it. Each control commits changes by callback. Browser verifies 123 survives Options → Greeks → Dashboard → Options → Scenario. Provider values never transfer. |
| M03 | Shared notebook editor in Discovery and Stock Explorer | One exchange-qualified listing key and v2 JSON schema; research question, thesis, source/date, counterevidence, trigger and review status. Shared revisioned exports; v1 restore supplies the new thesis field. No database persistence or fabricated issuer registry. Apple/Microsoft SEC identifiers preserved; other issuers require manual matching. |
| M04 | Options scenario; `test_negative_option_volatility_shock_is_rejected_visibly` | Negative resulting volatility is rejected with a visible error; no silent floor. Exactly zero is intentionally supported by deterministic pricing. |
| M05 | Stock Explorer selected-view dropdown; browser mount/request measurement | Only one chosen official widget is mounted; notes/history mount none. Consent preserved and revocable. Local cold widget script requests fell from 6 to 1. Timings are observations, not a provider speed guarantee. |
| M06 | `requirements.in`, `.lock`, `.txt`, `requirements-dev.txt`, Docker digest, CI | Exact transitive runtime versions and base image digest; direct tool pins and verified action commit pins. CI covers dashboard, browser workflow, dependency/static/history scans, pricing/auth/403 Docker smoke. Lock is version-pinned, not a hash-verified wheelhouse. |
| M07 | `dashboard/build_info.py`, About; `scripts/release_manifest.py`; CI artifacts | Nonsecret source SHA/Python/runtime versions visible; release record includes source SHA and lock hash. Exact live deployment remains unverified until an approved deployment and host attestation. Source checkout identity is truthfully distinguished from artifact identity. |
| M08 | `mean_correlation`; constant-history regressions | Undefined pair correlation returns `None` if any included variance is zero or pair results are nonfinite; single asset also None. Finite JSON-safe risk summaries. |
| M09 | Main and direct Discovery entry reduced to contained routing; `news_engine.py` | Hosted legacy stock/news page bodies/imports removed. Historical helpers retained in Git history; offline provider adapters never enabled by a flag. RSS adapter uses defusedxml with DTD/entities/external references forbidden and streamed 1 MB bound. Network-denial/market-403 regressions retained. |
| L01 | Options sensitivity uses `st.text` | Literal currency signs remain plain text instead of Markdown math. Browser workflow exercises the page; full assistive-technology certification is not claimed. |
| L02 | Per-record delete; archive help; strict JSON restore | Delete frees capacity; archive explicitly continues to count toward 50. Restore validates format, listing uniqueness, fields, status, HTTPS URL, lengths, count and total bytes before replacing state; explicit replacement checkbox. Invalid import is all-or-nothing. Boundary regressions cover archive/delete/re-add. |
| L03 | Home advanced links and Simulation Lab | Scanner primary alias replaced by Simulation Lab; old routes still redirect. Duplicate simulation option calculator replaced by link to canonical Options workspace. |
| L04 | Official copyright markup in chart/detail embeds | Removed forced attribution font size and app anchor colors; retained official copyright link markup. Exact operator/branding rights still await provider review. |

## Mathematics and QA follow-ups

- Scalar and vectorized Black–Scholes use log(S) − log(K), avoiding underflowing
  spot/strike division. Extreme-ratio and independent reference tests verify behavior.
- Core `greeks()` retains full precision before repricing/contract multiplication.
  Existing API JSON responses retain their four-decimal presentation convention;
  no downstream mathematical function uses those response-rounded values.
- Monte Carlo shows the constant-weight daily-rebalanced assumption beside its heading,
  differentiating the static-unit buy-and-hold historical chart. Loss probabilities
  include a Wilson sampling interval (including all-zero/all-one tail observations),
  tail sample count and editable seed. Parameter/model uncertainty remains additional;
  VaR/ES are not worst-case limits or validated real-market forecasts.
- Scenario Explorer now shares the canonical model, supports joint spot/volatility/time
  shocks and long/short quantities, and reports theoretical 100-share-contract P/L.
  Expiry and zero-volatility follow the tested engine; no provider data is ingested.
- Public-company/fictional-use boundaries remain; no visibility/secrets/deployment changes.

## Evidence and limitations

See `qa/evidence` for the compact review evidence record and actual fictional exports.
The original complete report and large audit logs remain outside the source repository.
CI status and exact review head are recorded in the PR and final implementation handoff.
Tests attest tested source/runtime only. No claim is made that the live app contains
these unmerged changes or that a separately hosted API has been protected.

Manual residuals: actual host/runtime attestation, written host/provider review,
real-device and assistive-technology spot-checks, revocation behavior with owner/Michael,
all external widget filter/indicator/unsupported-listing combinations, and host retention.
No accounts or invitations were altered to simulate these checks.

## Owner verification and deployment

Follow A–D gates and the deployment/rollback procedure in `BUILD_AND_RELEASE.md`.
Review saved revision and exact download bytes, compare two listings, and independently
check owner/Michael and signed-out access. Keep sensitive records out of every surface.
This PR must not be auto-merged or treated as production authorization.
