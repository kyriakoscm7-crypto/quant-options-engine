"""Source-linked SEC financial intelligence for Guided and Analyst research."""

import os
from datetime import date

import requests  # noqa: F401 - shared HTTP transport patched by offline tests
import streamlit as st

from app.intelligence.sec_access import sec_get

COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{}.json"

CONCEPTS = {
    "Revenue": (
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "Revenues",
        "SalesRevenueNet",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
    ),
    "Net income": ("NetIncomeLoss",),
    "Operating cash flow": ("NetCashProvidedByUsedInOperatingActivities",),
    "Capital spending": ("PaymentsToAcquirePropertyPlantAndEquipment",),
}

EXPLANATIONS = {
    "Revenue": "How much the business earns from selling products or services.",
    "Net income": "Profit remaining after expenses and taxes.",
    "Operating cash flow": "Cash generated or used by day-to-day operations.",
    "Free cash flow": (
        "Operating cash flow minus spending on property, plant and equipment. "
        "This is a simplified measure, not a complete assessment of cash available."
    ),
}


@st.cache_data(ttl=3600, show_spinner=False)
def load_company_facts(cik: str, user_agent: str) -> dict:
    """Retrieve one bounded SEC financial dataset, cached for one hour."""
    if not cik.isdigit() or len(cik) != 10:
        raise ValueError("Invalid SEC company identifier.")

    if not user_agent or "@" not in user_agent:
        raise ValueError("Configure a genuine SEC administrative contact.")

    response = sec_get(
        COMPANYFACTS_URL.format(cik),
        headers={
            "User-Agent": user_agent,
            "Accept": "application/json",
        },
        timeout=20,
        stream=True,
    )

    try:
        response.raise_for_status()
        chunks = []
        size = 0

        for chunk in response.iter_content(chunk_size=65536):
            size += len(chunk)
            if size > 30_000_000:
                raise ValueError("SEC financial response exceeded size limit.")
            chunks.append(chunk)

        import json

        payload = json.loads(b"".join(chunks))
        if str(payload.get("cik", "")).lstrip("0") != cik.lstrip("0"):
            raise ValueError("SEC company identity mismatch.")

        if not isinstance(payload.get("facts"), dict):
            raise ValueError("Financial data is unavailable.")

        return payload
    finally:
        response.close()


def annual_series(payload: dict, concepts: tuple[str, ...]) -> list[dict]:
    """Use comparable full-year observations reported in annual filings."""
    us_gaap = payload.get("facts", {}).get("us-gaap", {})

    for concept in concepts:
        values = (
            us_gaap.get(concept, {})
            .get("units", {})
            .get("USD", [])
        )

        by_period = {}

        for row in values:
            try:
                if row.get("form") not in ("10-K", "10-K/A"):
                    continue
                if row.get("fp") != "FY":
                    continue

                start = date.fromisoformat(row["start"])
                end = date.fromisoformat(row["end"])
                filed = date.fromisoformat(row["filed"])

                if not 330 <= (end - start).days <= 400:
                    continue
                if end > date.today() or filed > date.today():
                    continue

                val = row["val"]
                if isinstance(val, bool) or not isinstance(val, (int, float)):
                    continue

                record = {
                    "end": end.isoformat(),
                    "value": val,
                    "filed": filed.isoformat(),
                    "accession": row.get("accn", ""),
                    "concept": concept,
                }

                previous = by_period.get(record["end"])
                if previous is None or record["filed"] > previous["filed"]:
                    by_period[record["end"]] = record

            except (KeyError, TypeError, ValueError):
                continue

        if by_period:
            return sorted(
                by_period.values(),
                key=lambda item: item["end"],
                reverse=True,
            )

    return []


def number(value: float | None) -> str:
    if value is None:
        return "Not available"
    magnitude = abs(value)
    if magnitude >= 1e12:
        return f"${value / 1e12:,.2f}T"
    if magnitude >= 1e9:
        return f"${value / 1e9:,.2f}B"
    if magnitude >= 1e6:
        return f"${value / 1e6:,.1f}M"
    return f"${value:,.0f}"


def percent(value: float | None) -> str:
    return "Not available" if value is None else f"{value:.1f}%"


def filing_url(cik: str, accession: str) -> str | None:
    clean = accession.replace("-", "")
    if not clean.isdigit() or len(clean) != 18:
        return None
    return (
        "https://www.sec.gov/Archives/edgar/data/"
        f"{int(cik)}/{clean}/"
    )


def render_financial_intelligence(company) -> None:
    """One evidence base, presented at two different depths."""
    st.markdown(
        """
        <style>
        .qi-intel-kicker {
            color: #FF78B7;
            letter-spacing: .14em;
            font-size: .73rem;
            font-weight: 750;
            margin-top: 1rem;
        }
        .qi-intel-heading {
            font-size: clamp(1.65rem, 3vw, 2.45rem);
            color: #FFFFFF;
            letter-spacing: -.04em;
            font-weight: 750;
            line-height: 1.15;
            margin: .35rem 0;
        }
        .qi-intel-desc {
            color: #AEBED5;
            font-size: .95rem;
            margin: .4rem 0 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.caption("QUANT INTELLIGENCE / FINANCIAL RESEARCH")

    agent = os.getenv("QI_SEC_USER_AGENT", "").strip()
    if not agent:
        st.info(
            "Official financial research is not connected. "
            "Set QI_SEC_USER_AGENT in the server environment."
        )
        return

    try:
        with st.spinner("Reading official financial statements..."):
            facts = load_company_facts(company.cik, agent)
    except Exception:
        st.warning(
            "Financial statements could not be retrieved. "
            "Existing charts and official filing links are still available."
        )
        return

    series = {
        label: annual_series(facts, tags)
        for label, tags in CONCEPTS.items()
    }

    revenue = series["Revenue"]
    net = series["Net income"]
    cash = series["Operating cash flow"]
    capex = series["Capital spending"]

    if not revenue:
        st.info(
            "Comparable annual revenue data was not found in standard "
            "SEC financial concepts for this company. We will not "
            "estimate missing figures."
        )
        return

    current = revenue[0]
    fiscal_end = current["end"]
    previous = revenue[1] if len(revenue) > 1 else None

    net_row = next((r for r in net if r["end"] == fiscal_end), None)
    cash_row = next((r for r in cash if r["end"] == fiscal_end), None)
    capex_row = next((r for r in capex if r["end"] == fiscal_end), None)

    growth = None

    if previous and previous["value"] != 0:
        gap = (
            date.fromisoformat(fiscal_end)
            - date.fromisoformat(previous["end"])
        ).days

        if 330 <= gap <= 400:
            growth = (
                (current["value"] / previous["value"]) - 1
            ) * 100

    margin = (
        net_row["value"] / current["value"] * 100
        if net_row and current["value"] != 0
        else None
    )

    free_cash = (
        cash_row["value"] - capex_row["value"]
        if cash_row and capex_row
        else None
    )

    guided, analyst = st.tabs([
        "Understand the business",
        "Analyst workspace",
    ])

    with guided:
        with st.container(border=True):
            st.markdown("#### Financial health at a glance")
            st.caption(
                f"Latest comparable full-year statements · "
                f"Year ended {fiscal_end}"
            )

            a, b, c = st.columns(3)
            a.metric(
                "Annual revenue",
                number(current["value"]),
                percent(growth) if growth is not None else None,
            )
            b.metric("Net profit margin", percent(margin))
            c.metric("Free cash flow", number(free_cash))

            st.caption(
                "Revenue growth compares consecutive comparable annual "
                "periods. Margin is net income divided by revenue. "
                "Free cash flow is operating cash flow less capital spending."
            )

        with st.container(border=True):
            st.markdown("#### What do these numbers tell us?")

            if growth is None:
                st.write(
                    "**Growth:** A reliable year-over-year comparison "
                    "is not available."
                )
            elif growth > 0:
                st.write(
                    f"**Growth:** Annual revenue increased by "
                    f"{growth:.1f}% compared with the previous "
                    "comparable year. The business generated more sales, "
                    "but this alone does not establish why."
                )
            elif growth < 0:
                st.write(
                    f"**Growth:** Annual revenue declined by "
                    f"{abs(growth):.1f}% compared with the previous "
                    "comparable year. Investigate the company's "
                    "explanation and business conditions."
                )
            else:
                st.write(
                    "**Growth:** Annual revenue was essentially "
                    "unchanged from the previous comparable year."
                )

            if margin is not None:
                st.write(
                    f"**Profitability:** The company reported about "
                    f"${margin:.2f} in net income for every $100 of "
                    "revenue during this fiscal year."
                )
            else:
                st.write(
                    "**Profitability:** A comparable annual net "
                    "income figure is unavailable."
                )

            if free_cash is not None:
                st.write(
                    f"**Cash generation:** Simplified free cash flow "
                    f"was {number(free_cash)}. Compare this with "
                    "prior years and debt obligations before drawing "
                    "conclusions about financial strength."
                )
            else:
                st.write(
                    "**Cash generation:** The information needed "
                    "to calculate comparable free cash flow "
                    "was not available."
                )

        with st.container(border=True):
            st.markdown("#### What matters next?")
            st.write(
                "Investigate whether sales growth is supported by "
                "profits and cash generation, whether the trend is "
                "improving over several years, and what management "
                "has disclosed about major risks."
            )
            st.caption(
                "These are research questions, not an investment "
                "recommendation or a prediction of stock returns."
            )


    with analyst:
        import plotly.graph_objects as go

        st.markdown("### Financial performance")
        st.caption(
            f"Fiscal year ended {fiscal_end} · Reported USD · "
            "Annual financial statements"
        )

        latest_net = net_row["value"] if net_row else None
        latest_cash = cash_row["value"] if cash_row else None

        a, b, c, d = st.columns(4)

        a.metric(
            "Annual revenue",
            number(current["value"]),
            percent(growth) if growth is not None else None,
        )
        b.metric("Net income", number(latest_net))
        c.metric("Operating cash flow", number(latest_cash))
        d.metric("Free cash flow", number(free_cash))

        st.markdown("#### Revenue over time")

        points = list(reversed(revenue[:6]))
        years = [item["end"][:4] for item in points]
        values = [item["value"] / 1e6 for item in points]

        figure = go.Figure()

        figure.add_trace(
            go.Scatter(
                x=years,
                y=values,
                mode="lines+markers",
                line=dict(color="#FF78B7", width=3),
                marker=dict(size=8, color="#FF78B7"),
                fill="tozeroy",
                fillcolor="rgba(255,120,183,0.07)",
                hovertemplate=(
                    "FY%{x}<extra></extra>"
                    "<br>Revenue: $%{y:,.1f}M"
                ),
            )
        )

        figure.update_layout(
            height=330,
            margin=dict(l=10, r=15, t=15, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#AEBED5"),
            xaxis=dict(
                title=None,
                type="category",
                showgrid=False,
                tickangle=0,
            ),
            yaxis=dict(
                title="USD millions",
                tickprefix="$",
                ticksuffix="M",
                gridcolor="rgba(174,190,213,0.12)",
                rangemode="tozero",
                zeroline=False,
            ),
            showlegend=False,
        )

        st.plotly_chart(
            figure,
            width="stretch",
            config={"displayModeBar": False},
        )

        st.markdown("#### What stands out?")

        observations = []

        if growth is not None:
            direction = "increased" if growth >= 0 else "declined"
            observations.append(
                f"Revenue {direction} by {abs(growth):.1f}% "
                "compared with the previous comparable year."
            )

        if latest_net is not None:
            if latest_net < 0:
                observations.append(
                    "The company reported a net loss for "
                    "the latest fiscal year."
                )
            else:
                observations.append(
                    "The company reported positive net income "
                    "for the latest fiscal year."
                )

        if (
            latest_cash is not None
            and latest_net is not None
            and latest_cash > 0
            and latest_net < 0
        ):
            observations.append(
                "Operating cash flow was positive despite "
                "the reported net loss. The cash-flow "
                "statement can help explain this difference."
            )

        if free_cash is None:
            observations.append(
                "Comparable free cash flow is unavailable "
                "because one or more required figures are missing."
            )

        if observations:
            with st.container(border=True):
                for observation in observations:
                    st.markdown(f"- {observation}")

        st.caption(
            "These observations describe reported figures. "
            "They do not establish causes or predict stock returns."
        )

        st.markdown("#### Annual financial statements")

        rows = []

        for period in revenue[:6]:
            end = period["end"]
            n = next((r for r in net if r["end"] == end), None)
            c = next((r for r in cash if r["end"] == end), None)
            x = next((r for r in capex if r["end"] == end), None)

            rows.append({
                "Fiscal year": end[:4],
                "Revenue": number(period["value"]),
                "Net income": number(n["value"] if n else None),
                "Operating cash flow": number(
                    c["value"] if c else None
                ),
                "Capital spending": number(
                    x["value"] if x else None
                ),
                "Free cash flow": number(
                    c["value"] - x["value"]
                    if c and x else None
                ),
            })

        st.dataframe(
            rows,
            hide_index=True,
            width="stretch",
        )

        st.caption(
            "Missing values are displayed as Not available. "
            "Figures are abbreviated for readability."
        )

        with st.expander("Sources, methods & financial concepts"):
            for label, records in series.items():
                if not records:
                    continue

                item = records[0]
                st.write(
                    f"**{label}:** {item['concept']} · "
                    f"Period ended {item['end']}"
                )

                source_url = filing_url(
                    company.cik,
                    item["accession"],
                )

                if source_url:
                    st.link_button(
                        f"View source for {label}",
                        source_url,
                    )

            st.caption(
                "Uses annual SEC 10-K observations with "
                "approximately 12-month reporting periods. "
                "Figures may be restated. Some company-specific "
                "concepts, foreign filings and non-USD reporting "
                "are not covered. Free cash flow is calculated "
                "as operating cash flow less capital spending "
                "when both figures are available."
            )
