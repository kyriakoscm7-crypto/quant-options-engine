"""Private research workspace disclosures and draft website policies.

These are operational transparency documents, not a substitute for
professional legal review or required data licensing.
"""

import streamlit as st

DISCLOSURE = """
### Financial research disclosure

Quant Intelligence is an independent educational software and portfolio project
developed by Kyriakos Margaritis. It demonstrates quantitative methods through
real-stock display widgets, fictional simulations and illustrative calculators. It does not provide
personalized investment, brokerage, legal, or tax advice, and its operators
do not act as an investment adviser through this service.

No output should be treated as a recommendation to buy, sell, or hold
a security or as a statement that an investment is suitable for anyone.
Do not base investment decisions solely on this platform.

**Data limitations:** TradingView charts are external display widgets. Their
prices can be delayed, missing, stale, adjusted, or incorrect. Fictional simulation
inputs and model outputs are not actual market observations.
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

**Status:** Private research workspace. Last revised November 3, 2026.

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
visible. Use only provider-supported chart features. Do not scrape, bulk-extract
or repurpose widget data for models,
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

**Status:** Private research workspace. Last revised November 3, 2026.

This notice describes this private educational research build. Access restriction
is configured in Streamlit Community Cloud, not enforced by this page.
It does not certify the practices of an earlier deployed version. Hosting configuration and actual
retention still require operator verification before release.

**Information entered into the app.** Visitors choose stocks for external
charts and may enter hypothetical calculator values and fictional portfolio
quantities. Streamlit controls send inputs to the app server and use session
state. The app has no user registration, brokerage linking, payments or
application-level database of visitor portfolios in these public flows. Do not enter real account
numbers, passwords, government IDs, sensitive financial records or
other confidential personal information. Use invented amounts rather than your actual
income, debts, savings or holdings. The educational controls do not need real records.

**Technical data.** Streamlit hosting and other infrastructure
providers may process connection metadata, IP addresses, cookies,
security logs or usage diagnostics under their own terms and notices.
The repository requests that Streamlit usage telemetry be disabled;
[Community Cloud documentation](https://docs.streamlit.io/deploy/streamlit-community-cloud/status)
says the host overrides this preference and hosts apps in the United States.
Do not assume the repository setting disables host telemetry. See also
[Streamlit privacy information](https://docs.streamlit.io/develop/concepts/configuration/options#telemetry).
Actual host settings, log retention and subprocessors still require verification.

**External research panels.** Charts, financials, company profiles, technical ratings and news panels are off initially. If you allow automatic panels in Stock Explorer or the top-right Settings menu, the chart and company research, including panels in unselected tabs, load automatically when you enter Stock Explorer during that session. Your browser
connects directly to TradingView. Its widget FAQ states that widgets process the
embedding page URL, widget type, displayed symbol and IP address, and do not set
cookies. See [TradingView's widget FAQ](https://www.tradingview.com/widget-docs/faq/general/)
and [privacy policy](https://www.tradingview.com/privacy-policy/).
TradingView’s broader privacy policy also describes device and usage analytics, including third-party analytics providers. Private, invitation-only login does not itself constitute consent to these external requests. This choice lasts for the session. You can disable further chart loads in
Settings. This switch prevents future chart loads; it cannot undo prior requests.
The app does not receive provider panel data or use it in custom analytics. Research notes are your own text, processed by the Streamlit server, kept in session state and downloadable; they are not permanent account storage or sent to TradingView.

**Session controls.** The chart-loading choice resets with a new session. Closing a
browser tab disconnects it but is not a verified deletion request for host logs.
The operator must verify how long disconnected sessions and diagnostic logs persist.

**Purposes.** Inputs are processed to display calculations and
research outputs; technical information may be processed for service
delivery, security and diagnostics. No sale of personal data is intended.

**Sharing and location.** Third-party hosting and data services may
process certain data outside Canada. The operator must verify any
relevant transfer, retention and disclosure arrangements.

**Contact and requests.** For privacy/access requests, suspected errors or
content-rights concerns, contact the operator, Kyriakos Margaritis, at
[Kyriakoscm7@gmail.com](mailto:Kyriakoscm7@gmail.com). Describe the affected
page and concern without sending account credentials or sensitive records.
Do not post sensitive information in public GitHub issues.

**Security.** No internet service can promise perfect security.
The platform is not intended to receive sensitive financial or
identity information.

This notice must be updated if registration, analytics, payments,
portfolio persistence, brokerage integration or other data-handling
features are introduced.
"""


def render_legal_pages() -> None:
    st.title("About, Privacy & Legal")
    st.caption("Quant Intelligence / restricted, independent engineering research workspace")
    st.markdown(
        "Developed by **Kyriakos Margaritis** to teach financial concepts and "
        "demonstrate quantitative software engineering. Real-stock charts are "
        "provided by TradingView; custom risk, screening and forecast examples "
        "use fictional inputs. No broker affiliation or provider endorsement is implied."
    )
    st.link_button("View source & methodology ↗", "https://github.com/kyriakoscm7-crypto/quant-options-engine")
    disclosure, terms, privacy = st.tabs(
        ["Financial disclosure", "Terms of use", "Privacy"]
    )
    with disclosure:
        st.markdown(DISCLOSURE)
    with terms:
        st.markdown(TERMS)
    with privacy:
        st.markdown(PRIVACY)
    st.info(
        "Your viewer list and sign-in requirements are administered in "
        "Streamlit Community Cloud → Sharing. This application does not "
        "implement its own account management or revoke hosting access. "
        "Keep the list restricted to your approved collaborators."
    )
    st.caption(
        "Outstanding operator review: verify hosting terms, market-data "
        "permissions and actual privacy practices. These disclosures "
        "are not a substitute for applicable legal advice."
    )
