# Quant Intelligence — private research workspace

This release is designed for a very small, invited development/review group.
It is **not** a self-hosted login system or a grant of data rights.

## Access and collaboration

- The app is restricted in **Streamlit Community Cloud → App settings → Sharing**.
  The app UI does not authenticate visitors, maintain its own allowlist,
  revoke access, or inspect who signed in.
- Keep the active viewer list to the owner and Michael, using their
  actual authenticated accounts. Use separate GitHub access permissions
  for source-code collaboration; app viewer access does not grant code access.
- Verify access with a signed-out/incognito browser and one authorized
  device. A private Streamlit app is not a guarantee that invited viewers
  cannot invite additional people; periodically review the viewer list.
  If a strict owner-only allowlist is mandatory, consider an external
  access gateway on hosting whose terms suit the application.
- Never put credentials, secrets, private keys, real holdings, account
  numbers, or client financial information into the UI, issue tracker or
  repository. Use hypothetical numbers for every portfolio/calculator.
- The gear in the top-right is **local session preferences**, not access
  control. Display density, research tips and TradingView chart opt-in can
  be changed or reset there. Legal/Privacy/About are also linked there.
- Never describe the demo data or model scores as verified real-stock
  trading signals. No brokerage or portfolio-account connection exists.

## Keep the technical project impressive

- Real stocks: official, attributed TradingView embedded chart; loading
  requires a visitor's session opt-in. It is display-only and does not
  feed custom quant engines.
- Risk and research: deterministic synthetic OHLCV + existing real math
  (beta, volatility, Sharpe, drawdown, technical scoring, screening).
- Options, Greeks, hypothetical scenarios and Quant Learn remain fully
  interactive and usable with manually supplied illustrative inputs.
- Portfolio Manager now includes an experimental Monte Carlo risk panel:
  correlated synthetic return paths, adjustable time horizon, illustrative
  Value-at-Risk and Expected Shortfall, and a probability-of-loss chart.
  The model assumes rebalanced weights and multivariate normal log returns,
  using only fictional market histories. It is not a prediction of actual
  securities and is not designed for brokerage-account values.
- Existing real-data development pipelines remain in the repository for
  appropriately authorized experimentation. Private hosting does not
  authorize redistribution, derived-output display or all uses of yfinance.
- Do not remove data-rights guards or unlock legacy Yahoo HTTP routes
  based only on a login, a secret environment variable or a small guest list.

## Release checklist

1. Confirm Streamlit sharing is private and check all current viewers.
2. Review the provider and Cloud hosting terms for this intended use.
3. Run CI, automated Streamlit-route tests and the direct-page/API tripwires.
4. Preview desktop and phone layouts, top-right settings, TradingView attribution
   and opt-out, direct Discovery page, synthetic disclaimers and Options Lab.
5. Verify API market-data routes remain unavailable without provider access.
6. Merge/deploy only with owner approval and retest the authenticated and
   unauthenticated experience. An app update does not itself alter sharing.
7. Reassess licensing and regulatory requirements before enabling real-data
   quantitative analytics, subscriptions, invitations beyond the trusted group,
   personalized recommendations, brokerage access or real-money execution.

Private access reduces exposure, **not legal responsibility**. Data-provider
rights, hosting terms, market-advice obligations and privacy rules remain
independent questions.


Stock Explorer UX update: the disclosed session opt-in now allows automatic
chart and research loading on entry/return. No Load chart button remains.
Simple company labels retain exchange-qualified internal symbols. Explicit
lookback controls set the provider range separately from candle interval.
Quote overview and chart remain visible above selected research/notes; the
research tabs include financials, company background, technicals and news. See STOCK_EXPLORER.md
for the range mapping, privacy assessment and data-rights limits. Sharing and
hosting configuration have not changed.


The original-layout follow-up restores the earlier Stock Explorer control row and
Performance / Risk & Scores / News / Historical Data tabs, with an additional
notes tab. All research-tab panels load after the same session consent. See
ORIGINAL_EXPERIENCE_PARITY.md for preserved features, data limitations and hosting
checks that still require operator verification. No repository edit claims that
production access or all applicable legal requirements have been verified.
