"""Public-facing research disclosures and draft website policies.

These are operational transparency documents, not a substitute for
professional legal review or required data licensing.
"""

import streamlit as st

DISCLOSURE = """
### Financial research disclosure

Quant Intelligence provides independent research, quantitative analysis,
illustrative calculators, and educational material. It does not provide
personalized investment, brokerage, legal, or tax advice, and its operators
do not act as an investment adviser through this service.

No output should be treated as a recommendation to buy, sell, or hold
a security or as a statement that an investment is suitable for anyone.
Do not base investment decisions solely on this platform.

**Data limitations:** Prices, corporate information, third-party headlines,
and historical data can be delayed, missing, stale, adjusted, or incorrect.
Displayed values are not necessarily executable prices. Users should
confirm material information with appropriate primary sources.

**Model limitations:** Research scores use experimental assumptions and
weights. They have not been established to predict future returns.
Option values and simulated profit/loss are theoretical; calculations
may not account for exercise style, transaction costs, bid/ask spreads,
taxes, liquidity, early assignment, dividends, or market disruptions.
Backtests and simulations are not actual trading results.

Financial markets involve risk, including loss of invested capital.
Consider consulting an appropriately registered professional for
advice tailored to your circumstances.
"""

TERMS = """
### Terms of use

**Status:** Public beta. Last revised November 3, 2026.

By using this site, you agree to use it for lawful, personal research
and educational purposes only. If you disagree with these terms,
please stop using the site.

**No advisory or brokerage relationship.** Quant Intelligence does not
accept trading instructions, execute orders, hold user funds, or
offer individualized investment advice. Access to any research or
calculation does not establish a professional advisory relationship.

**No guarantees.** The service and its calculations are provided on
an as-available, as-is basis, to the extent permitted by applicable law.
Models can contain defects and may yield inaccurate or incomplete
outputs. Availability and content may change without notice.

**Independent verification.** You are responsible for checking data,
assumptions and outputs before relying on them. Do not use this service
as your sole basis for financial decisions.

**Acceptable use.** Do not abuse the service, interfere with access,
attempt unauthorized access, submit malicious content, or use third-party
data in violation of applicable rights or restrictions.

**TradingView charts.** External charts are display-only widgets governed by
[TradingView terms](https://www.tradingview.com/policies/). Attribution must remain
visible. Do not scrape, extract, export or repurpose widget data for models,
trading systems or redistribution. Availability and delays vary by exchange.

**Third-party material.** Financial data, articles and external
websites may be subject to separate licences and terms. Third-party
trademarks belong to their owners. References do not imply endorsement.

**Liability.** To the extent permitted by applicable law, the
operators disclaim warranties and liability for loss arising from
the use of, or inability to use, this research tool. Nothing here
excludes liability or consumer rights that cannot lawfully be
excluded. This clause requires jurisdiction-specific legal review.

**Changes.** Features and terms may be updated as the service develops.
Continued use after posted updates may be subject to updated terms,
as permitted by applicable law.

**Governing rules.** Mandatory consumer, privacy and securities laws
continue to apply regardless of any disclaimer.
"""

PRIVACY = """
### Privacy notice

**Status:** Public beta. Last revised November 3, 2026.

This notice describes how the current experimental web interface is
designed to operate. Hosting and infrastructure practices still need
to be verified before broader public promotion.

**Information entered into the app.** Visitors may enter stock tickers,
hypothetical options inputs, and example portfolio holdings. The
portfolio editor currently uses Streamlit session state; it is not
designed as a persistent brokerage account. Do not enter real account
numbers, passwords, government IDs, sensitive financial records or
other confidential personal information.

**Technical data.** Streamlit hosting and other infrastructure
providers may process connection metadata, IP addresses, cookies,
security logs or usage diagnostics under their own terms and notices.
The operator must verify actual retention periods and subprocessors.

**External charts.** When external charts are enabled (the default), your browser
connects directly to TradingView. Its widget FAQ states that widgets process the
embedding page URL, widget type, displayed symbol and IP address, and do not set
cookies. See [TradingView's widget FAQ](https://www.tradingview.com/widget-docs/faq/general/)
and [privacy policy](https://www.tradingview.com/privacy-policy/).
Disable loading in Legal / Settings / About before visiting Stock Explorer if
preferred. This switch prevents future chart loads; it cannot undo prior requests.
The app does not receive chart prices or use them in its custom analytics.

**Purposes.** Inputs are processed to display calculations and
research outputs; technical information may be processed for service
delivery, security and diagnostics. No sale of personal data is intended.

**Sharing and location.** Third-party hosting and data services may
process certain data outside Canada. The operator must verify any
relevant transfer, retention and disclosure arrangements.

**Rights and requests.** Privacy and access requests should be handled
through a private contact method supplied by the operator. Do not
post sensitive information in public GitHub issues. A dedicated privacy
contact must be published before the app is promoted to users.

**Security.** No internet service can promise perfect security.
The platform is not intended to receive sensitive financial or
identity information.

This notice must be updated if registration, analytics, payments,
portfolio persistence, brokerage integration or other data-handling
features are introduced.
"""


def render_legal_pages() -> None:
    st.title("Legal & About")
    st.caption("Quant Intelligence / research and educational platform")
    disclosure, terms, privacy = st.tabs(
        ["Financial disclosure", "Terms of use", "Privacy"]
    )
    with disclosure:
        st.markdown(DISCLOSURE)
    with terms:
        st.markdown(TERMS)
    with privacy:
        st.markdown(PRIVACY)
    st.warning(
        "Operator review pending: verify market-data licensing, hosting "
        "and privacy practices, add a private privacy contact, and have "
        "the terms reviewed for applicable law."
    )
