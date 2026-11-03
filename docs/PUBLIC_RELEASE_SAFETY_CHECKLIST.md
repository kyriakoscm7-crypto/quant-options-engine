# Quant Intelligence — Public release safety review

Last updated: November 3, 2026. This is an engineering and legal review checklist, not legal clearance.

## Immediate deployment safeguard
- [x] Stock Explorer uses the official display-only TradingView chart embed. Other data-sensitive public research routes use **synthetic interactive demos**, without Yahoo API calls on those render paths.
- [x] Preserve self-contained educational and hypothetical options tools.
- [x] Describe experimental technical indicators as historical classifications rather than investment advice.
- [x] Provide prominent in-app disclosure and accessible draft terms/privacy notice.
- [ ] The legacy rights flag cannot unlock public analytics. Select and review a provider with explicit public-display and derived-data rights before implementing a separate integration.

## Blocking tasks before broadly promoting the site
- [ ] Obtain an explicit written market-data licence or use a provider whose terms affirm public web display and the intended use. Investigate Yahoo Finance/yfinance, third-party news, company metadata, exchange listings and derived data. Free APIs do not necessarily permit redistribution.
- [ ] Audit other entry points / APIs (including FastAPI endpoints, Streamlit pages and command-line jobs) for unlicensed external data access or redistribution. Current UI safeguard does not certify non-Streamlit services.
- [ ] Complete a privacy/data-flow audit of Streamlit hosting logs, analytics, session state, subprocessors, retention and any data transfers; publish a private privacy-contact email. Update privacy wording to match observed behavior.
- [ ] Have a Canadian securities lawyer assess the research scores, model outcomes, marketing, subscription plans, personalized recommendations and whether registration or exemptions apply in the jurisdictions served.
- [ ] Have counsel review Terms of Use and limitations of liability. They cannot eliminate mandatory rights or all liability.
- [ ] Verify model input validation, stale data and source timestamps, mathematical correctness, and that simulations exclude real trading fees and execution constraints unless incorporated.
- [ ] Check copyright/trademark rights for icons, images, news snippets and third-party content.
- [ ] Review hosting security, dependencies, error messages, secrets, logging, user upload restrictions, incident response and applicable insurance.
- [ ] After explicit deployment approval, test all public routes on the actual host, including direct-page URLs, mobile layouts, chart attribution, unavailable symbols and external-chart loading controls. Confirm no backend market-data requests occur.
- [ ] Keep any real trading, account connectivity and individualized buy/sell advice disabled pending separate compliance review.

## Developer notes
The public Streamlit interface routes Stock Explorer to an official TradingView embed and Discovery, Market Scanner, Portfolio Manager and Forecast Intelligence to locally generated fictional data regardless of the legacy rights flag. The direct Quant Discovery page is also protected. Analytics, models, portfolio examples, charts and filters stay interactive. The original market-data engines and third-party source integrations remain in the private/development code paths but are *not* authorized for public redistribution by this change. Do not treat an offline demo as proof of legal compliance or model predictive validity.

The synthetic companies, ticker-like symbols, seeded OHLCV series, screening scores and forecast comparisons are fictional. Public visitors must see the demo disclosure before viewing any synthetic chart. Real-stock charts retain provider branding and a nearby delay/availability notice. Do not collect real brokerage holdings, account credentials or other sensitive financial information in Community Cloud.

You can run local tests using `python -m pytest tests/test_public_safety.py -q`. Do not enable the rights flag just to make a deployment look complete.

## TradingView display-only review
See [current official sources and integration boundary](TRADINGVIEW_AND_PROVIDER_RIGHTS.md).
- [ ] Operator reviews/accepts applicable widget terms and confirms the intended hosting/use is permitted; resolve any ambiguity with TradingView.
- [ ] Verify embedded charts on the intended host, with attribution fully visible at mobile and desktop sizes.
- [ ] Do not infer real-time exchange entitlements from a TradingView subscription.
- [ ] No merge or deployment without explicit user go-ahead.
