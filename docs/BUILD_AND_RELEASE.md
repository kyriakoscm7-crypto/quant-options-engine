# Reproducible review and phased release

Production base: `3611d515b22b87a323785320bfafa8ed41748a31`.
Preserve `backup/quant-prod-2026-11-04-87be3e3`, PR #6 and all existing branches.
The backup points to an older build with legacy paths: it is historical evidence,
**not the preferred rollback target**.

## Build discipline (M06/M07)

`requirements.in` describes direct dependencies; `requirements.lock` pins the entire
previously audited Python 3.11 Linux runtime set, plus defusedxml and patched setuptools.
`requirements.txt` includes that lock for Streamlit and Docker. This is a reviewed
version lock, not a hash-verified wheelhouse. Host OS/platform and Python must match;
Python 3.15 may require different wheels and is not the deployment target.

For an update, resolve in a disposable Python 3.11 environment, regenerate the complete
lock, review every version/license/security change, run pip check, full tests, browser
QA, dependency audit and Docker gates, then submit a separate PR. Do not silently
upgrade direct or transitive packages during deployment. CI tools have direct pins;
their transitive environment is not the application runtime lock.

Docker uses a resolved official multi-platform Python 3.11 image digest. Build with
`docker build --build-arg BUILD_SHA=$(git rev-parse HEAD) -t qi:<reviewed-sha> .`.
Record the resulting image digest/ID and retain it without moving its release tag.
The API container defaults to production and will not start without a strong token.
Local API development requires `QI_API_MODE=development` and a loopback-only bind;
remote clients are rejected even in that mode. Do not run local mode behind a public proxy.

About displays only nonsecret source identity and live package/Python versions.
A checkout SHA is explicitly labeled as source evidence, not host attestation.
Set `QI_BUILD_SHA` in a reviewed artifact build. Never insert the old production SHA
into a modified artifact. `scripts/release_manifest.py` records source SHA, lock hash
and runtime packages; CI uploads a unique per-run release record and image ID.
Download and archive these with the eventual host deployment ID/log, timestamp,
reviewer and privacy/auth evidence. No deployed build is certified by this PR.

## Acceptance and deployment gates

A — correctness/containment: independently verify first-day loss/entry/chart;
submit the final note field without blur, wait for its saved revision, download that
revision and inspect actual JSON bytes. Test every home card; invalid negative
volatility must produce an error. Preserve network-denial/legacy-403 tests.

B — integrated research: use two listings and independent browser sessions.
Discover → save notes → Stock Explorer → Options → Greeks → Dashboard → Options →
Scenario → return. Verify listing identity, model assumptions, shared notes/revisions,
validated v1/v2 restore and deletion/50-record/archive semantics. A reload/new tab is
an intentionally new Streamlit session; export before leaving. In-app buttons preserve
session state; compatibility query links cannot make a new browser connection durable.

C — operational discipline: all CI gates green for the exact reviewed head; archive
release record, lock and image ID. Resolve external host/API/provider evidence in
EXTERNAL_REVIEW.md. Actual Streamlit runtime versions must match the reviewed manifest,
or investigate and retest. Do not assert a protected public API without its host test.

D — presentation/performance: capture 390/400/768/1440 widths, check essential controls,
keyboard focus and visible attribution; test reduced motion and consent withdrawal.
Compare external widget-script requests, mounted widget counts and cold/warm timings
against the audited snapshot without inspecting provider content. Provider outages
or unsupported listings must not be replaced by invented company metrics.
Real-device/assistive-technology checks and arbitrary third-party filter combinations
remain manual acceptance; desktop emulation does not certify them.

## Later owner-approved deployment

1. Review this fix PR and its exact head/checks. Do not merge automatically.
2. Obtain separate owner approval for a deployment window and unresolved constraints.
3. Create a new backup of the then-current production SHA; preserve historical backup.
4. Release staged A/B/C/D scope with reviewed dependencies, never a blind cherry-pick
   of interdependent files. Set nonsecret build metadata and record host deployment ID.
5. Keep Sharing private. Owner and Michael independently verify access and workflow;
   a signed-out clean profile must show no app contents. Test a revoked invitation
   only with explicit owner coordination; no accounts are changed by this PR.
6. Verify About SHA/runtime against the archived record and inspect actual downloads.
7. If failed, use a reviewed Git revert of the new release to the immediately preceding
   contained production commit (3611d51 if unchanged). Do not force-push, change Sharing,
   or restore the older Yahoo-enabled backup. If API protection fails, isolate that
   service through its operator; do not disable authentication to restore availability.
8. Preserve logs/artifact IDs and reassess before retrying. No production action has
   been performed as part of implementation.

### PerpEquities release hold (2026-11-05)

The optional PerpEquities integration is disabled by default. With
`QI_PERPEQUITIES_ENABLED` unset (or any value other than `true`), Stock Explorer
omits its market-size panel and search works without its ranking data. The shared
snapshot entry point rejects access before reading the cache or sending a request.
Keep the flag unset in production. Do not enable it until third-party public data
usage rights and the intended host's eligibility have been reviewed and resolved.
This gate does not constitute permission to merge or deploy; the release hold
remains in place pending those decisions.

Local validation of the browser correction and gate: 2,080 pytest tests passed;
Ruff, pip check, independent numerical/API checks, pip-audit, Bandit at the CI
severity threshold, and reachable-history secret scan passed. The complete
Chromium acceptance workflow passed at 390, 400, 768 and 1440 pixels, including
shared notebook exports and session isolation. All ten isolated news scenarios
passed at 390 and 1440 pixels. No app layout changes were needed: a fresh Stock
Explorer session defaults to SPY without a notebook record, while existing
shortlisted-company notes remain editable.
