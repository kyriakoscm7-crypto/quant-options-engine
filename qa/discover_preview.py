"""Local UI acceptance fixture. Never imported by production routing."""
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import streamlit as st

from app.intelligence.company_identity import CompanyIdentity
from dashboard import discover_intelligence as ui

st.set_page_config(page_title="Discover QA fixtures", layout="wide")
st.markdown(f'<style>{(Path(__file__).parents[1] / "dashboard/premium_theme.css").read_text()}</style>', unsafe_allow_html=True)
st.warning("SYNTHETIC QA FIXTURES — interface testing only. No real issuer facts, rankings or live provider connection.")


def brief(_gateway, ticker):
    if ticker == "QAERROR":
        raise RuntimeError("QA provider unavailable")
    ratios = {"Current ratio": 2, "Liabilities / assets": .5,
              "Net margin": .2, "Operating cash / revenue": .3}
    if ticker == "QABETA":
        ratios.update({"Net margin": -.2, "Current ratio": .5})
    missing = ticker == "QAMISSING"
    observations = {key: {"metric": key, "value": value, "unit": "USD",
                          "start": "2025-10-01", "end": "2026-09-30",
                          "filed": "2026-11-01", "accession": "synthetic-qa-only",
                          "url": "https://example.test/synthetic-qa-only"}
                    for key, value in {"revenue": 1_000_000_000, "income": 200_000_000,
                                       "operating_cash": 300_000_000}.items()}
    report = {
        "company": CompanyIdentity(ticker, f"Synthetic {ticker}", "0000000001"),
        "health": {"period": datetime.now(UTC).date().isoformat(),
                   "ratios": {} if missing else ratios, "observations": {} if missing else observations,
                   "issues": ["Missing comparable annual facts"] if missing else [],
                   "status": "synthetic QA fixture"},
        "sources": [], "filings": [], "issues": [],
        "earnings": {"status": "unavailable", "evidence": []},
        "analysts": {"status": "unavailable", "evidence": []},
    }

    if os.environ.get("QI_QA_FACTORS") == "1":
        from app.intelligence.fundamental_factors import factor_research
        from qa.factor_fixture import payload
        data = payload()
        if missing:
            data['facts'] = {}
        report['research'] = factor_research(data, 1, sic=3571, as_of=datetime.now(UTC).date())
    return report


with patch.dict(ui.os.environ, {"QI_SEC_USER_AGENT": "QA fixture — gateway disabled"}), \
     patch.object(ui, "_gateway", lambda _: None), \
     patch.object(ui, "company_deep_dive", brief), \
     patch.object(ui, "UNIVERSES", {"Synthetic QA set": ("QAALPHA", "QABETA", "QAMISSING")}):
    ui.render_intelligence()
