# Discover clarity and reliability follow-up

## Shipped behavior

- A short, plain-language banner explains each research lens and company section. Research lenses use visible radio controls rather than a dropdown. Company analysis uses Overview, Trends, 8 factors, Stress and Evidence tabs (short labels fit mobile screens). The core factor table and scenario controls are directly visible in their tabs; detailed methodology remains collapsed.
- Cards use plain metric labels, distinguish required-pattern coverage from overall factor coverage, show the share-growth date window and explicitly state that independent-source corroboration has not run.
- Share CAGR no longer stitches observations across filing accessions. It uses the latest contiguous comparative suffix from one annual filing, requires at least three comparable annual observations, and retains the actual-year CAGR formula. A shorter window is disclosed; insufficient comparable data stays unavailable. No split ratio is guessed. This may reduce Improving fundamentals eligibility; weights, anchors, other formulas and sector exclusions are unchanged.
- Evidence & checks includes internal agreement between the existing research and financial-health extraction paths. Only identical tags, units, start/end and accession are compared. This is the same input payload, not independent verification.
- An explicit **Check original annual filing** action fetches one recent annual original SEC document through the same user-agent validation, pacing, cooldown, bounded cache, size limits and no-redirect policy. It compares tagged original-document observations with Company Facts for the same accession, tag, period, entity and unit. No external HTML resources execute or load. Unsupported numeric transforms, dimensional contexts, entity/period/unit differences and conflicting duplicate facts remain unresolved. Outcomes distinguish exact agreement, agreement within declared XBRL rounding, discrepancy, conflicting filing facts and not comparable. Results never replace source values or scores. Failed refresh clears old check results; discrepancies remain visible beside the candidate and company score.
- A leave-one-factor-out diagnostic recomputes the mean of the remaining selected factors. The minimum/maximum show dependence on individual inputs, not confidence intervals, expected returns, a validated accuracy estimate or a replacement score. Anchor-boundary counts explain clipped extremes.

## Why the share guard matters

The supplied screenshot shows NVIDIA share CAGR of 76.7%. The original engine selected the latest-known value separately for each annual period, allowing old pre-split counts to mix with newer split-adjusted comparative counts across a five-period history. Same tags and units alone do not prove a common share basis.

NVIDIA's FY2026 original 10-K, Note 4, publishes diluted weighted-average shares of 24,940 million (Jan 28, 2024), 24,804 million (Jan 26, 2025) and 24,514 million (Jan 25, 2026). It states that presented share amounts are retrospectively adjusted for the ten-for-one split. These three published observations give approximately −0.86% annual growth over their actual elapsed time. This is a documented two-year endpoint window, not a replacement five-year estimate or an injected production value. The regression fixture uses these published numbers; production continues to require fetched evidence.

Primary references:
- [NVIDIA original FY2026 10-K, Note 4 and split disclosure](https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm)
- [NVIDIA split 8-K](https://www.sec.gov/Archives/edgar/data/1045810/000104581024000144/nvda-20240607.htm)
- [NVIDIA investor-relations annual report directory](https://investor.nvidia.com/financial-info/annual-reports-and-proxies/default.aspx)
- [SEC API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)

## Verification and honest source limits

- Full suite: 2,189 tests passed; focused reliability/Discover suite: 109 passed. Existing dependency warnings remain.
- Regression cases include mixed split bases, safe comparative suffixes, published NVIDIA share arithmetic, missing years, source contexts, unit/entity/accession mismatches, decimal scale/sign/rounding, conflicting facts, source failure, response bounds, safe SEC URLs and cooldown preservation.
- Real Chrome on isolated synthetic QA fixtures: search, compare, drilldown/back, labeled tabs, keyboard scenario changes, factor evidence, sensitivity output, original-check failure state and 390/768/1440-pixel geometry/overflow. Screenshots in `docs/images/discover-reliability/` were visually inspected and do not assert live issuer verification.
- Project Ruff, dependency compatibility, whitespace and targeted Bandit medium/high checks passed.
- Public primary documents were consulted for the NVIDIA audit. A fresh live gateway/document-parser end-to-end check was not run: this environment has no genuine configured SEC operator contact. The parser is deliberately narrow, and real filing formats can yield not comparable. Successful matches in synthetic tests are not live-source evidence.

SEC Company Facts, an original SEC-hosted filing, and an issuer-hosted copy share the same issuer origin. Matching them can catch extraction discrepancies, but cannot establish independent economic truth or a probability of correctness. No paid service, independent vendor, earnings feed or analyst feed was connected. More websites repeating the same filing do not create additional independent sources. A future additional source must have compatible metric definitions, fiscal periods, units, currency and corporate-action basis, public-use rights and dated attribution; discrepancies must be surfaced rather than averaged away. No provider rights or live cross-provider accuracy are claimed here.

No merge or deployment. Existing legal/privacy boundaries remain in place. This revision adds only a user-triggered original SEC-document check, not arbitrary URL retrieval or a new data-provider integration.
