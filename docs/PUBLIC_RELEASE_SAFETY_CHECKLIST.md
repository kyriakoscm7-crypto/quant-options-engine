# Release safety checklist

The current review and release gates are in [Production readiness — November 2026](PRODUCTION_READINESS_2026_11.md), with [official source-rights evidence](SOURCE_RIGHTS_2026_11.md).

- [x] Work remains on draft PR #6; no production merge/deploy or access-list changes.
- [x] Hosted legacy market-data routes remain disabled, independent of environment attestations.
- [x] Discovery and Stock Explorer use official opt-in display widgets; no app extraction/ranking of provider data.
- [x] Discovery supports user-authored evidence shortlists and comparisons without invented metrics.
- [x] Synthetic Forecast/Portfolio and simulations are grouped in Quant Lab.
- [x] Mathematical pricing/Greeks/scenarios and research engines preserved.
- [ ] Verify final-commit CI, target-host rendering and accessibility.
- [ ] Verify production branch and commit: live inventory currently shows `quant-intelligence-automation`, not `main`.
- [ ] Verify exactly owner and Michael, including inherited GitHub permissions and anonymous denial.
- [ ] Resolve hosting eligibility, provider/operator terms and actual privacy practices.
- [ ] Obtain explicit owner approval for exact release commit and target branch.

Detailed older audit documents are historical context where they differ from the current review. Private access is not a market-data licence or guarantee of compliance.
