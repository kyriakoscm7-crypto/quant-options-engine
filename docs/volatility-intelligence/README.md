# Volatility Intelligence

Stock Explorer now places an offline educational Plotly surface between historical prices and financial explanations. Every searchable symbol can access it, including symbols with no listed options. The symbol is research context only: inputs and defaults are identical across companies. No external data or new dependency is required.

The existing Plotly 3D module supplies the shared navy/pink volatility palette. Its legacy data collector import is now confined to its command-line entry point; importing the visualizations does not load that collector. Observed-quote preparation and scatter semantics remain intact.

## Model and limits

Annualized hypothetical volatility in percentage points is:

`clip(level - skew * ln(K/S) + curvature * ln(K/S)^2 + term * ln(days/30), 1, 200)`

The reference strike at 30 calendar days anchors the baseline. The fixed grid is 49 moneyness points from 0.7 to 1.3 and 40 maturities from 7 to 365 calendar days. Inputs are bounded and finite. The model is illustrative, not calibrated, arbitrage-free, or predictive. It uses no observed company prices, options, earnings or fundamentals. Controls persist between symbols; camera orientation persists during updates. The 2D alternative supports touch exploration and browsers without usable WebGL.

All views and hover labels say SIMULATION. Authorized chain upload is deliberately deferred: no observed-IV mode or implied provenance is offered without a separate validated data workflow.

## Verification

- Numerical formula, invalid/boundary inputs, plot semantics, symbol independence, controls, and exact integration position are covered in `tests/test_volatility_intelligence.py`.
- `qa/volatility_preview.py` runs the production Stock Explorer with external panels disabled and company data renderers stubbed, so browser tests do not require providers or credentials.
- `qa/volatility_browser.py` checks widths 390, 768 and 1440, surface/heatmap rendering, slider interactions, section order, exceptions and horizontal overflow. The existing CI browser job includes this regression and uploads screenshots.
- No deployment workflows, branch protections, provider configuration, SEC, earnings or Neon behavior are changed.
