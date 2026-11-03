# Quant Intelligence — Public release safety review

Last updated: November 3, 2026. This is an engineering and legal review checklist, not legal clearance.

## Immediate deployment safeguard
- [x] Public Streamlit market-data routes are gated OFF by default until source rights are verified.
- [x] Preserve self-contained educational and hypothetical options tools.
- [x] Describe experimental technical indicators as historical classifications rather than investment advice.
- [x] Provide prominent in-app disclosure and accessible draft terms/privacy notice.
- [ ] **DO NOT set QI_MARKET_DATA_RIGHTS_CONFIRMED=true** unless counsel/operator has confirmed rights for every displayed public market-data feed. The flag is not a licence.

## Blocking tasks before broadly promoting the site
- [ ] Obtain an explicit written market-data licence or use a provider whose terms affirm public web display and the intended use. Investigate Yahoo Finance/yfinance, third-party news, company metadata, exchange listings and derived data. Free APIs do not necessarily permit redistribution.
- [ ] Audit other entry points / APIs (including FastAPI endpoints, Streamlit pages and command-line jobs) for unlicensed external data access or redistribution. Current UI safeguard does not certify non-Streamlit services.
- [ ] Complete a privacy/data-flow audit of Streamlit hosting logs, analytics, session state, subprocessors, retention and any data transfers; publish a private privacy-contact email. Update privacy wording to match observed behavior.
- [ ] Have a Canadian securities lawyer assess the research scores, model outcomes, marketing, subscription plans, personalized recommendations and whether registration or exemptions apply in the jurisdictions served.
- [ ] Have counsel review Terms of Use and limitations of liability. They cannot eliminate mandatory rights or all liability.
- [ ] Verify model input validation, stale data and source timestamps, mathematical correctness, and that simulations exclude real trading fees and execution constraints unless incorporated.
- [ ] Check copyright/trademark rights for icons, images, news snippets and third-party content.
- [ ] Review hosting security, dependencies, error messages, secrets, logging, user upload restrictions, incident response and applicable insurance.
- [ ] Test all public routes and confirm gating behavior on the actual hosted Streamlit app.
- [ ] Keep any real trading, account connectivity and individualized buy/sell advice disabled pending separate compliance review.

## Developer notes
The market-data safeguard applies to the public Streamlit interface and direct Quant Discovery page. It intentionally does not rewrite historical analytics engines or prove rights to underlying market data. It is a temporary fail-closed measure. Research features can be restored when compliant data and permissions are in place.

You can run local tests using `python -m pytest tests/test_public_safety.py -q`. Do not enable the rights flag just to make a deployment look complete.
