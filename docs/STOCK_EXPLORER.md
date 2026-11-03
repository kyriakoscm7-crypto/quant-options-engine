# Stock Explorer data boundary and methodology

The real-stock view uses TradingView's official Advanced Chart widget. Candles,
volume, indicators, date ranges and provider symbol search stay inside that
provider-hosted display. Attribution is preserved; external loading is opt-in.
No chart values, messages, DOM, screenshots or network responses are read by the
application to drive analytics. The outer company selector controls every panel; chart-local symbol changes are disabled to prevent mismatched company research.

The integrated workbench restores analytical interactions, not company research:
- Reproducible geometric Brownian paths for fictional Model A and Model B.
- Indexed comparison, realized sample return, annualized sample volatility,
  drawdown, Sharpe (zero risk-free rate), beta and correlation using the shared
  risk engine. Internal `beta_vs_spy` key is reused for Model B; no SPY feed.
- Initial-weight buy-and-hold blends, drawdown plots and manual allocation shocks.
- Manual European Black–Scholes pricing, dividend yield, analytical Greeks and
  expiry P&L per share using the existing pricing engine.
- Fictional CSV export and links to external research destinations.

Synthetic sample dates are computational alignment labels only; plots use
observation numbers. The selected company never changes fictional paths.
No predictive probabilities, company ranks or invented news are presented.

## Provider rights

Checked November 3, 2026:
- https://www.tradingview.com/widget-docs/faq/data/ describes delayed stock data,
  symbol restrictions and absence of an export/data API.
- https://www.tradingview.com/widget-docs/faq/general/ describes attribution,
  sizing and connection metadata.

No alternative free API is added. Before adding one, verify intended private or
public display, storage, historical use, derived analytics, redistribution,
exchange requirements, attribution, audience limits and commercial use against
its actual agreement. Free access alone is insufficient.

Automatic real-stock KPI cards, historical risk, comparisons, technical scores,
forecasts, fundamentals, downloadable history and ingested/reprinted news remain
disabled pending separately verified data and content permissions. The original
engines remain available in the codebase. External links do not license copying.
This design reduces specific exposure; it is not legal clearance or immunity.

## Validation and release

Tests cover deterministic paths, valid input bounds, allocation endpoints,
company/model isolation, parameter responsiveness, option interaction, and all
existing public-route HTTP isolation tests. CI lints the new calculation/UI
modules and runs the complete suite. Review both desktop/mobile and actual widget
availability in the target environment before release. Hosting config is unchanged.
PR #6 must remain draft; merge/deployment require explicit approval.

## Real-stock research update

Stock Explorer now focuses exclusively on actual symbols: chart, symbol overview,
financials, company profile, technical analysis and related news in official
TradingView display-only panels. After opt-in, the quote overview and chart stay open. Chart/Overview also open financials and company background; other views select a research panel beneath the chart. Arbitrary exchange-qualified symbols are supported, subject to provider
availability. Missing data never falls back to synthetic numbers. These panels
follow TradingView's documented multi-widget stock-page integration:
https://www.tradingview.com/widget-docs/tutorials/iframe/build-page/widget-integration/

The fictional workbench is no longer rendered in Stock Explorer. Its calculation
module and tests remain for optional educational use. The earlier list of rights
limitations refers to app-computed/downloaded data, not information that the
provider makes available within its own display panels. No provider data is
extracted, stored or transformed into custom company analytics. Technical ratings
are the provider's indicator summary, not a Quant Intelligence recommendation.

My analysis stores user-written notes separately for each symbol during the
session and supports Markdown download. Notes survive research-view changes;
a new browser session is not permanent storage. Text is processed by the hosted
Streamlit server; notes are not transmitted into TradingView widgets. Simulation
Lab remains explicitly fictional and now links directly to real Stock Explorer.


## Automatic workspace and lookbacks (November 3, 2026)

Company labels use `Apple · AAPL`; internal symbols remain `NASDAQ:AAPL`.
The chart opens automatically on entry and return after the visitor enables
TradingView for the session, without a separate Load chart button. No persistent
cookie, shared consent, hosting secret or inferred consent from login is added.
Reset preferences or disabling Settings removes every provider embed. Notes
remain available without opting in. Each new Streamlit session asks again.

The official **Legacy Advanced Chart** configurator (the iframe embed in use)
exposes Default data range separately from Default interval:
https://www.tradingview.com/widget-docs/widgets/charts/legacy-advanced-chart/
The official embedding script explicitly accepts `range` and `interval`:
https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js
Checked the configurator's generated iframe configuration for `range: "1D"`;
its preview switched to one-minute bars even with a daily default interval.
Do not apply the separately licensed Charting Library's APIs to this widget.

| App lookback | Provider range | Requested candle interval |
| --- | --- | --- |
| 1D | 1D | 1 minute |
| 1W | 5D | 15 minutes |
| 1M | 1M | 30 minutes |
| 3M | 3M | 1 hour |
| 6M | 6M | Daily |
| 1Y | 12M | Daily |
| 5Y | 60M | Weekly |
| All | ALL | Monthly |

1W means five trading days, not an exact seven-calendar-day boundary. 1D uses
the latest available trading day; closed sessions, listings and provider history
limits affect coverage. TradingView may choose candle resolution for its range.
The chart toolbar changes candle size; it does not select the lookback. Panning
or zooming changes visible history. Selecting a different app lookback recreates
the embed. No app-derived date boundary or fabricated price history is shown.

### Privacy assessment

Private access for the owner and Michael is preserved, but host authentication
is not evidence of either viewer's informed choice about a separate provider.
Canadian consent guidance emphasizes explaining what is shared, with whom and
why, and giving a meaningful choice before unexpected third-party disclosure:
https://www.priv.gc.ca/en/privacy-topics/privacy-for-businesses/appropriate-handling-of-personal-information/collecting-personal-information-and-consent/consent/gl_omc_201805/
PIPEDA applicability depends on commercial activity and personal/domestic-use
exceptions; private hosting alone does not settle this, nor provincial or other
applicable rules. We retain explicit per-session opt-in rather than assume an
exemption or treat the owner's request as Michael's consent. The first-use toggle
and Settings explain automatic loading, IP, symbol, widget type and embedding URL,
link the provider policy, and permit withdrawal. The widget FAQ's no-cookie claim
is presented alongside the broader policy's device/usage analytics disclosure:
https://www.tradingview.com/privacy-policy/
This is an engineering safeguard, not a determination of legal compliance.

No licensed data feed has been added: custom real-stock KPI calculations,
historical exports, forecasts and app-ingested news still require separately
verified data/content rights. Attribution and official provider panels remain.
