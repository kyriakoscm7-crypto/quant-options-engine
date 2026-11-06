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
- Earnings: Finnhub US calendar adapter is implemented for authorized personal local use or a written provider agreement. Key setup and authenticated live verification remain operator steps. Dates are unconfirmed because this provider does not distinguish company-confirmed versus estimated dates. See [calendar setup and limitations](EARNINGS_CALENDAR.md).

## Calendar integration boundary

The weekly adapter is isolated from `APPROVED_SOURCES` and the financial evidence/scoring engine. Calendar events never enter scores or the notebook. It uses a fixed official host, explicit operator usage scope, server-only credentials, short memory caching, bounded retries and visible incomplete/error states. SEC identity is resolved when opening research. No calendar result is promoted to confirmed financial evidence. For keys, rights, date semantics and staging validation, use [EARNINGS_CALENDAR.md](EARNINGS_CALENDAR.md).

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
