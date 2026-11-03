# Stock Explorer data boundary and methodology

The real-stock view uses TradingView's official Advanced Chart widget. Candles,
volume, indicators, date ranges and provider symbol search stay inside that
provider-hosted display. Attribution is preserved; external loading is opt-in.
No chart values, messages, DOM, screenshots or network responses are read by the
application to drive analytics. Widget symbol changes do not synchronize to the
outer company selector or model lab.

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
