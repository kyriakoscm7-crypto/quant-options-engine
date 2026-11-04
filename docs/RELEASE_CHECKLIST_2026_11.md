# Private research release candidate — November 3, 2026

**Decision: HOLD. Draft PR #6 only. No merge or deployment authorized.**

## Candidate scope

One Discovery workspace: Scan uses the official opt-in provider screener; Investigate focuses on exact listings, primary-source links and a session shortlist. The compact shortlist provides status, questions and review triggers in a table; detailed notes collapse; comparison and JSON export remain user-authored research only. Shortlisted listings open Stock Explorer directly. There is no screener extraction or backend price ingestion.

Quant Lab prioritizes Options, Greeks and scenarios. Model testing contains the preserved hypothetical strategy, simulation, forecast and portfolio engines. Stock Explorer's risk shortcut opens Options with listing context only. Options and Greeks explicitly transfer manual assumptions in both directions. Sub-dollar Greeks scenarios now keep the underlying positive; local sensitivities explain units and limitations.

## Recorded branch baseline (remote read November 3)

| Ref | SHA | Meaning |
| --- | --- | --- |
| `main` | `b2d7295adaf48197e9695757ed0eb90eda401651` | PR base |
| `quant-intelligence-automation` | `87be3e364e4ca7cc7acc0fb00b54ce61ca0e1c45` | Previously observed live host branch; rollback reference subject to owner reconfirmation |
| PR #6 before this pass | `30d2ee83b43c9e17c6494589814184e1930df204` | Audited starting point |

The production branch contains one merge commit beyond the shared base; `git diff main quant-intelligence-automation` was empty at inspection. Do not assume the refs remain unchanged. The candidate is not deployed by merging PR #6 to main alone under the previously observed host configuration.

## Review locally

1. Start a fresh loopback Streamlit process from this checkout; imported modules in an older process can remain stale. Use port 8520 if the earlier previews on 8510/8511 are still running.
2. Open Discovery. Scan should show a consent choice before any provider frame. Investigate should focus on listings and notes. Add Apple/Microsoft; change status; expand evidence; record a reporting period and counterevidence; compare and download. Verify selection changes and navigating away do not lose records. A new session must start empty.
3. Open the shortlisted exact listing in Stock Explorer. Check company identity and SEC search coverage manually. With explicit opt-in, inspect attribution, technical ratings, delayed/unavailable symbols, chart range/style and settings revocation. A frame's own state is not an app-verified historical sample.
4. Use the risk shortcut to Options. Confirm only ticker context transfers, with default/manual numerical assumptions. Change a call/put, spot, strike, volatility, rate, dividend, days and contracts; transfer to Greeks and back. Try spot 0.25 and a downward movement. Inspect repricing versus local approximation; neither is an executable quote.
5. Inspect desktop and 390px layout, keyboard focus/skip link, settings gear and table scrolling. Screenshots in `docs/images/release-2026-11/` document local QA; full screen-reader and target-host checks remain outstanding.
6. Review final-head Python CI (Ruff, full tests, security audit) and Docker CI, not an earlier green commit. Confirm draft remains open, no auto-merge and no credentials/research exports in the diff.

## Mandatory gates before asking for release approval

- [ ] Written host eligibility resolution for heightened-protection/financial-information restriction and exact private hosting arrangement.
- [ ] Provider/operator terms review or confirmation covering the exact two-person use; attribution and display-only restrictions preserved.
- [ ] Owner reconfirms actual host repository, entrypoint, Python version, branch and deployed SHA. Source refs alone do not verify the currently running binary.
- [ ] Only intended two users have access, including inherited repository permissions. Test anonymous and uninvited signed-in denial. No viewer or visibility changes are authorized here.
- [ ] Confirm host logs, retention, processing location, subprocessors and incident contact. Keep account/portfolio/personal financial records out of notes.
- [ ] Separate API remains private; before any exposure require strong token, TLS and proxy limits. Streamlit authentication does not secure FastAPI.
- [ ] Final target-host provider, mobile, keyboard and assistive-technology acceptance checks.
- [ ] Owner approves exact candidate SHA, target branch, release action and recorded rollback SHA explicitly. No approval is implied by this checklist.

## Proposed release/rollback path — do not execute yet

1. After gates close, fetch refs and compare against the baseline above; stop for unexpected production changes. Record current deployed commit as the rollback commit and preserve it with an owner-approved release tag if desired.
2. Approve a specific PR head and review its checks. Merge PR #6 into main only with explicit owner approval. Record resulting merge SHA; rerun checks for that SHA.
3. Because the host tracks `quant-intelligence-automation`, separately approve either a normal merge from approved main into that branch or an explicit host target change. The latter changes hosting configuration and needs separate approval. Prefer a reviewed normal merge to preserve history; never force-push. Inspect the complete production-branch diff and CI before the approved release action.
4. After approved deployment, verify access denial, consent defaults, source attribution, calculators and API isolation. Record host deployment SHA/time.
5. If acceptance fails, stop the rollout. With owner authorization, revert the release merge on the tracked deployment branch using its first parent; test the revert and deploy through the same approved path. Do not reset or rewrite shared history. Data/session notes are not durable backups and cannot be restored by a code rollback.

M20, production, hosting settings, repository visibility, viewers and secrets remain outside this implementation's mutations.
