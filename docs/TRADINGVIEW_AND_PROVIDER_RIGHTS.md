# Display widgets and future analytics data

Official documentation checked November 3, 2026. This records engineering constraints, not a legal opinion or a guarantee against claims. Recheck terms before release. No provider for backend real-stock analytics has been selected or licensed.

## Current implementation

Stock Explorer uses the official Advanced Real-Time Chart **embeddable widget**, not the separate Advanced Charts library. The official embed script runs in a Streamlit HTML component in the visitor's browser. TradingView serves the chart and controls symbol availability. The app does not read chart DOM, intercept messages, query undocumented endpoints, scrape, cache, export or pass chart prices/indicators to models. No proxy/feed adapter is introduced. The chart's symbol selection is independent of fictional simulation symbols. A visible external link remains available if embedding fails; no fictional prices silently replace the chart.

The dark theme uses documented widget settings. Provider logo, chart controls and copyright/link remain visible, with a 32px attribution area inside a 620px container and an enclosing 640px component. Branding is never covered or cropped intentionally. Test actual rendering on the intended host before release; automated Streamlit tests cannot execute the remote widget JavaScript.

The sidebar Legal / Settings / About popover provides policy access and an external-chart loading switch (off initially, enabled by the visitor for the session). Disabling removes future chart loads; it does not revoke already-sent requests. Financial research notices remain visible in the app and widget notices remain adjacent to charts. Full policies in a compact menu do not replace required point-of-use notices.

## Official sources and limits

- [Advanced chart widget and official embed configuration](https://www.tradingview.com/widget-docs/widgets/charts/advanced-chart/): offers embeddable charts. The widget documentation is the basis for this display integration, not a general redistribution licence. The operator must review applicable terms and intended use before release, and seek written clarification where needed.
- [TradingView terms, especially sections 3 and 4](https://www.tradingview.com/policies/): restrict processing/non-display use and redistribution; require attribution on externally used products/widgets to remain as designed. This integration does not obtain a separate licence for backend analytics, data redistribution or derived datasets.
- [Widget data FAQ](https://www.tradingview.com/widget-docs/faq/data/): availability varies; some symbols cannot be embedded. Stock quotes may be delayed. Paid TradingView plans do not change widget data entitlements. The widgets do not provide an API for extracting data/indicator values or feeding in our own data. Do not promise consolidated real-time exchange prices.
- [Available markets](https://www.tradingview.com/widget-docs/markets/): check current exchange-specific widget coverage and data levels, rather than assuming that a symbol on tradingview.com is embeddable.
- [North America coverage](https://www.tradingview.com/widget-docs/markets/north-america/): at review time, NASDAQ and NYSE stock widgets list Cboe One delayed data. This is not a promise of consolidated real-time quotes.
- [General widget FAQ](https://www.tradingview.com/widget-docs/faq/general/): says widgets do not set cookies, but process embedding URL, widget type, displayed symbol and IP. The privacy notice identifies this external connection; operator hosting/logging retention still requires review.
- [Advanced Charts datafeed API](https://www.tradingview.com/charting-library-docs/latest/connecting_data/datafeed-api/): the separate library contains no market data. Installing a charting library does not license a feed.

## Separate custom analytics boundary

Simulation Lab, Discovery, Scanner, Portfolio and Forecast continue using deterministic fictional inputs with visible simulation banners. Stock Explorer never combines real-stock widget prices with fictional model outputs. Even setting the old `QI_MARKET_DATA_RIGHTS_CONFIRMED=true` cannot unlock public legacy feeds. Original research modules remain for development, with no new rights granted by retaining the code.

Before connecting a provider, obtain written rights covering the intended audience/jurisdictions, exchange entitlements, public display, derived metrics/scores/forecasts, non-display computation, historical storage/caching, retention, exports, redistribution and attribution. Verify any restrictions on commercial use, user counts, delayed data and termination. Record the actual contract/version and implement timestamp, stale-data, access and export controls accordingly. Do not use retail subscriptions, yfinance availability or an operator checkbox as evidence of these rights.

## Remaining scope and release blockers

The Streamlit router, direct Quant Discovery entry point and standalone public analytics renderers use simulations. The legacy FastAPI options-data endpoint now returns HTTP 403 without provider access, irrespective of the legacy rights flag. CLI/research jobs and retained legacy provider modules are development tools, not authorized public data services; do not expose them as web endpoints or publish generated datasets without appropriate rights. The pre-existing real-stock forecast experiment CSV was removed from the deployment tree; past Git history has not been rewritten or cleared. Self-contained options/Greeks/scenario tools remain theoretical and educational. No broker connections, personalized advice or real-money execution are added. Legal review of securities obligations, Terms and Privacy, and verification of hosting practices remain release tasks. The operator-approved privacy/content contact is now published in-app. No merge or deployment is authorized.
