# Educational showcase: risk-reduction review

Reviewed November 3, 2026. This documents technical controls and current official
sources. It does not estimate lawsuit odds, certify compliance, or remove the
operator's responsibility for the actual deployed app. This work remains on draft
PR #6; no merge/deployment is authorized.

## Why change the data path?

[yfinance's own documentation](https://ranaroussi.github.io/yfinance/) identifies
it as unofficial and notes personal-use restrictions on Yahoo Finance's API.
That library's open-source availability is not a licence to redistribute downloaded
financial data. An educational purpose alone should not be treated as permission.
The precise applicable Yahoo/data-provider terms have not been cleared for this app.

By comparison, [TradingView explicitly offers widgets for supported markets](https://www.tradingview.com/widget-docs/markets/).
The implementation uses that documented display mechanism with provider-controlled
availability, intact attribution and no backend extraction. This gives the chart
display a clearer permission basis; it is not a quantifiable reduction in overall
lawsuit probability. [TradingView's terms](https://www.tradingview.com/policies/)
still apply, including attribution and restrictions on processing/non-display use.

## What public visitors can actually use

| Surface | Input/source | Boundary |
| --- | --- | --- |
| Stock Explorer | Official TradingView widget, after visitor chooses to load it | Browser display only; independent symbol search; no app export/feed/model access |
| Simulation Lab | Deterministic fictional OHLCV | Candlesticks, risk metrics, technical scores, fictional benchmark and methodology |
| Discovery / Scanner | Fictional universe | Experimental screening and charts, with visible simulation banners |
| Portfolio | Fictional instruments and example quantities | Session examples; no real holdings import, accounts, execution or brokerage linking |
| Forecast | Synthetic held-out comparisons | No claims of validated real-stock predictive performance |
| Options / Greeks / Scenarios / Learn | Hypothetical numerical inputs | Theoretical calculations and educational assumptions; no automated quote retrieval |
| FastAPI health/calculators | Validated hypothetical inputs | Calculations remain available; legacy third-party quotes route always returns 403 |

The direct Discovery page and direct public Portfolio/Scanner/Forecast renderers
also use simulations. The old rights flag cannot enable the legacy public feed.
Retained CLI/provider/research modules are development tools requiring appropriate
source rights, not public data services. A pre-existing real-stock experiment CSV
has been removed from the deployment tree and future outputs ignored. Prior Git
history has not been rewritten; previous publication is not retroactively cleared.

## Claims, privacy and contact

The About description identifies the independent educational software project and
its developer. No broker affiliation or provider endorsement is claimed. Company
presets are for exploration. The existing premium theme, educational labs and
quantitative engines remain available. Public notices identify delayed charts,
fictional inputs and theoretical results; full policies stay in the compact menu.
A disclaimer is an explanation, not immunity: [CSA/CIRO guidance](https://www.ciro.ca/newsroom/publications/joint-canadian-securities-administrators-and-canadian-investment-regulatory-organization-staff)
says registration requirements cannot be avoided merely by adding a disclaimer.
That guidance is relevant to online financial content but does not itself determine
this project's legal status. Monetization, referrals, personalized recommendations
or real-stock buy/sell rankings require a new assessment before introduction.

Charts start off and have a prominent one-click loading choice with an explanation
of the external connection. The session choice can be switched off. This is an
engineering privacy improvement, not a declaration that every applicable consent
requirement is satisfied. [TradingView's widget FAQ](https://www.tradingview.com/widget-docs/faq/general/)
identifies IP address, embedding URL, widget type and symbol processing. The
[Privacy Commissioner's consent guidance](https://www.priv.gc.ca/en/privacy-topics/privacy-for-businesses/appropriate-handling-of-personal-information/collecting-personal-information-and-consent/consent/gl_omc_201805/)
supports giving visitors clear information at the time of their choice.

Streamlit controls send input to the server; this is not an entirely local app.
No registration, payments or application-level database of visitor holdings is
introduced in these public flows. The contact address approved by the operator is
published in-app for privacy requests, suspected errors and content-rights concerns.
There is no promise of zero logs, tracking or retention. The repository requests
telemetry opt-out where honored; [Community Cloud documents an override and US hosting](https://docs.streamlit.io/deploy/streamlit-community-cloud/status).
Hosting retention, security and actual deployment behavior still need verification.

## What remains uncertain

Engineering changes cannot guarantee that a person will not file a claim or that
defending one would be cost-free. See the [subsequent end-to-end audit](END_TO_END_RISK_AUDIT.md) for a read-only
live-interface inspection and the additional bundled database removal. Applicable securities, privacy, consumer and contract obligations depend on
location, audience, actual operation and future claims/features. Professional legal
review would provide assurance this engineering review cannot. No company structure,
insurance coverage or jurisdiction-specific legal opinion has been obtained here.
Recheck provider terms and the intended host before an explicitly approved release.
