# Discover fundamental research engine

Implemented on `feature/discover-intelligence-v2`, extending PR #12. No merge or deployment.

## First slice

Up to eight user-selected SEC filers, using the existing paced/cached gateway and identity validation. Five most recent annual period ends, standard US-GAAP 10-K/10-K/A facts in USD (diluted weighted-average shares in shares). Cards explain the factors behind four selectable archetypes: quality compounders, improving fundamentals, cash generators, and loss-to-profit turnarounds to investigate. The selected company adds a compact operating/FCF margin trajectory, factor contributions, observation-level filing links, counterevidence and a user-controlled operating stress calculation.

The SEC documents Company Facts as standard-taxonomy, entity-wide observations, separated by units: https://www.sec.gov/search-filings/edgar-application-programming-interfaces . The engine further requires full annual duration (330–380 days), valid filing accession, period end ≤ filing date ≤ as-of date. Instant balance-sheet observations cannot have duration starts. No quarterly annualization or TTM synthesis.

## Calculation contract

- Revenue/share CAGR: actual elapsed years (365.2425 days/year), minimum three consecutive observations, 330–400 days between year ends, annual duration lengths within 14 days, positive values and unchanged tags. Missing intervening years prevent CAGR. Share CAGR now uses only the latest contiguous comparative suffix from a single filing accession (minimum three annual observations), to avoid mixing pre/post-split filing bases. Its explicit date window may be shorter than revenue history; no split multiplier is guessed.
- Operating margin = operating income / positive revenue. Change = last minus first over at least three consecutive observed years, unchanged numerator and denominator tags.
- FCF = CFO minus nonnegative `PaymentsToAcquirePropertyPlantAndEquipment`; CFO, capex and revenue must have identical period and accession. This is a narrow PP&E cash-flow proxy, not distributable cash, EBITDA or acquisition-adjusted cash flow.
- Cash conversion = CFO / positive net income. Nonpositive income gives unavailable, not a misleading negative conversion ratio.
- Balance sheet = liabilities / positive assets, identical instant period and accession. This is not debt or net debt.
- Earnings consistency = fraction of consecutive observed annual income values above zero, minimum three years; not earnings predictability or exceptional-item adjustment.
- Latest filing date wins independently per metric/end. Conflicting latest values/start/accession are excluded; revisions are disclosed. Cross-accession ratios are unavailable even if both components appear plausible. Comparative restatements may therefore reduce coverage. Evidence retains exact tags, units, dates and accessions.

Fixed lower/upper score anchors (decimal units) are revenue CAGR −.10/.20, margin change −.05/.05, operating margin 0/.30, FCF margin 0/.25, cash conversion .5/1.5, liabilities/assets .2/.9, share CAGR −.05/.05, earnings consistency 0/1. Higher is better except liabilities/assets and share CAGR. Clip the normalized value to [0,1], reverse lower-is-better, multiply by 100. These declared heuristic bounds winsorize extremes; they are not calibrated expected-return models. No empirical percentile, statistical confidence or optimized weights are asserted.

Archetypes average only their declared factors with equal weights and require every factor. Turnarounds additionally require first observed annual net loss and latest annual positive net income, not just rising margins. Missing is never scored as zero. Unknown SIC, financial/real-estate SIC 6000–6999, utilities 4900–4999, or an annual period older than 550 days prevents ranking. Other sectors use a generic model; no industry-specific calibration is implied. SIC is current issuer metadata, not historical classification. Broad exclusion is conservative rather than an exhaustive sector taxonomy.

## Comparisons and uncertainty

Users may inspect reported quantities side by side, with explicit accounting/period cautions. This small editorial/custom universe cannot establish valid peer distributions: no peer medians, z-scores, sector percentiles or market-wide ranking. Scores are pattern ordering within the requested scan; the ticker breaks exact ties. Coverage is observation count, not a probability of correctness. Every report remains a single issuer source and annual data may be old despite recent retrieval. Custom tags, IFRS, acquisitions, discontinued operations, fiscal-calendar changes and management adjustments need filing review.

The scenario is revenue × (1 + user revenue shock) × (reported operating margin + user margin shock in percentage points). It reports hypothetical operating income and change versus the reported baseline. It does not estimate taxes, financing, cash flows, valuation, price or forecast likelihood.

## Future catalyst/source integration

Use the existing `SourceGrant`/`Evidence` admission boundary. Before adding a feed, record provider and ultimate data owner, exact contract reference, licensed display/derived-use/storage/export rights, expiry, refresh budget, retention/deletion policy, attribution and timestamp precision. Admit issuer-confirmed IR announcements or a properly licensed earnings feed; estimated dates must remain separate. Distinguish event time, announcement/publication time, retrieval time, timezone and confirmation state. Resolve identity by verified CIK, expose conflicts and avoid counting syndication as independent corroboration. No provider, agreement or pricing has been selected or claimed.

Analyst consensus, market prices, valuation and live earnings calendars remain unavailable. Backtests require licensed timestamped price/total-return histories, corporate actions, survivorship-aware universes and archived facts with knowledge/acceptance timestamps. Filing-date filtering of today's revised Company Facts is tested as a cutoff, but cannot prove point-in-time historical availability. No new backtest or performance claim is offered.

## Verification

`tests/test_fundamental_factors.py` covers hand-calculated factors, bounds, units, currency, annual/quarterly contexts, accession mismatch, restatements, conflicts, future filings, missing years, tag switches, sector exceptions, stale data, nonpositive denominators and scenario math. `qa/factor_browser.py` exercises the isolated `QI_QA_FACTORS=1` synthetic preview; fixture code is never imported by production routing. Prior SEC/privacy/Stock Explorer tests stay in the full suite.

### Local verification for this revision

- Full suite: **2,155 passed**, 211 warnings (existing numerical/Pandas warnings plus three Streamlit chart Pandas deprecations).
- Factor-specific suite: **25 passed**, including scenario widget recalculation and missing-pattern filtering.
- Ruff, dependency consistency, whitespace checks, selected secret-history scan and Bandit medium/high gate passed.
- Independent pricing/Greeks/IV/API checks passed (500 generated numerical cases).
- Actual Chrome against isolated synthetic preview passed factor ranking, evidence expansion, scenario changes, missing evidence and no horizontal page overflow at 390/768/1440px. Captures are in `docs/images/discover-factors/` and are explicitly synthetic.
- No fresh live issuer retrieval was performed for this revision; prior PR live checks are historical evidence only. Gateway and identity/privacy regressions ran offline. Remote CI and deployment are separate from these local results.
