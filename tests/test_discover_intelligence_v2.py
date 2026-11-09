"""Offline Discover admission, normalization, orchestration and UX checks."""
import json
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from app.intelligence.discover_evidence import (
    Evidence,
    SourceGrant,
    corroborate,
    earnings_label,
)
from app.intelligence.discover_financials import financial_health
from app.intelligence.discover_sec import SecGateway
from app.intelligence.discover_service import company_deep_dive

CIK = "0000320193"
NOW = datetime(2026, 11, 5, 15, tzinfo=UTC)
ACC = "0000320193-26-000001"


def facts():
    values = {"Assets": 200, "Liabilities": 100, "AssetsCurrent": 80,
              "LiabilitiesCurrent": 40, "Revenues": 100,
              "NetIncomeLoss": 20, "NetCashProvidedByUsedInOperatingActivities": 30}
    data = {}
    for tag, value in values.items():
        row = {"val": value, "end": "2026-09-30", "filed": "2026-11-01", "form": "10-K", "accn": ACC}
        if tag in {"Revenues", "NetIncomeLoss", "NetCashProvidedByUsedInOperatingActivities"}:
            row["start"] = "2025-10-01"
        data[tag] = {"units": {"USD": [row]}}
    return {"cik": 320193, "facts": {"us-gaap": data}}


def row(payload, tag):
    return payload["facts"]["us-gaap"][tag]["units"]["USD"][0]


def test_annual_ratios_and_provenance():
    result = financial_health(facts(), CIK, today=NOW.date())
    assert result["ratios"] == {"Current ratio": 2, "Liabilities / assets": .5,
                                "Net margin": .2, "Operating cash / revenue": .3}
    assert result["status"] == "single source"
    assert result["observations"]["revenue"]["accession"] == ACC
    assert result["observations"]["revenue"]["unit"] == "USD"


@pytest.mark.parametrize("patch", [{"val": float("nan")}, {"val": True}, {"start": "2026-07-01"},
                                  {"form": "10-Q"}, {"filed": "2027-01-01"}, {"accn": "../evil"}])
def test_bad_duration_facts_never_enter_ratios(patch):
    payload = facts()
    row(payload, "Revenues").update(patch)
    result = financial_health(payload, CIK, today=NOW.date())
    assert "Net margin" not in result["ratios"]
    assert "revenue" not in result["observations"]


def test_no_currency_or_accession_or_period_mixing():
    payload = facts()
    row(payload, "AssetsCurrent")["accn"] = "0000320193-26-000002"
    row(payload, "Revenues")["end"] = "2025-09-30"
    payload["facts"]["us-gaap"]["Assets"]["units"]["EUR"] = payload["facts"]["us-gaap"]["Assets"]["units"].pop("USD")
    result = financial_health(payload, CIK, today=NOW.date())
    assert not result["ratios"]


def test_conflict_and_restatement():
    payload = facts()
    rows = payload["facts"]["us-gaap"]["Revenues"]["units"]["USD"]
    rows.append({**rows[0], "val": 110})
    result = financial_health(payload, CIK, today=NOW.date())
    assert "revenue" not in result["observations"]
    rows[1].update(filed="2026-11-04", form="10-K/A", accn="0000320193-26-000002")
    result = financial_health(payload, CIK, today=NOW.date())
    assert result["observations"]["revenue"]["value"] == 110
    assert "Net margin" not in result["ratios"]
    assert any("revised" in x for x in result["issues"])


def test_zero_denominator_missing_and_identity():
    payload = facts()
    row(payload, "LiabilitiesCurrent")["val"] = 0
    assert "Current ratio" not in financial_health(payload, CIK, today=NOW.date())["ratios"]
    with pytest.raises(ValueError, match="CIK"):
        financial_health(payload, "0000000001")
    assert financial_health({"cik": 320193}, CIK)["period"] is None


class Response:
    def __init__(self, data, status=200, headers=None):
        self.data, self.status_code, self.headers = data, status, headers or {}
        self.closed = False

    def iter_content(self, chunk_size):
        yield json.dumps(self.data).encode()

    def close(self):
        self.closed = True


def gateway(get):
    return SecGateway("Quant Intelligence research@operator.org", get=get, sleep=lambda delay: None)


def test_gateway_cache_identity_and_request_guards():
    calls = []
    response = Response({"cik": 320193})

    def get(url, **kwargs):
        calls.append(url)
        assert kwargs["allow_redirects"] is False
        assert "research@operator.org" in kwargs["headers"]["User-Agent"]
        return response

    client = gateway(get)
    first = client.fetch("companyfacts", CIK)
    first["data"]["cik"] = 0
    assert client.fetch("companyfacts", CIK)["data"]["cik"] == 320193
    assert len(calls) == 1 and response.closed
    for resource, cik in [("http://evil", CIK), ("submissions", "1"), ("directory", CIK)]:
        with pytest.raises(ValueError):
            client.fetch(resource, cik)


@pytest.mark.parametrize("status", [403, 429])
def test_gateway_cooldown_is_shared_across_resources(status):
    calls = []

    def get(*args, **kwargs):
        calls.append(1)
        return Response({}, status, {"Retry-After": "3600"})

    client = gateway(get)
    with pytest.raises(RuntimeError):
        client.fetch("directory")
    with pytest.raises(RuntimeError, match="cooldown"):
        client.fetch("submissions", CIK)
    assert len(calls) == 1


def grant(provider="a", owner="owner-a"):
    return SourceGrant(provider, owner, "fixture-contract-not-live", date(2027, 1, 1),
                       frozenset({"earnings", "analyst_sentiment"}), True, True)


def evidence(**kwargs):
    return Evidence(**{"cik": CIK, "field": "earnings", "value": "2026-11-06", "provider": "a",
                       "url": "https://provider.test/announcement", "as_of": NOW, **kwargs})


def test_earnings_proximity_and_unannounced_time():
    label = earnings_label(evidence(), now=NOW)
    assert label.startswith("1d") and "time unannounced" in label and "estimated" in label
    event = evidence(scheduled_at=datetime(2026, 11, 6, 1, tzinfo=UTC), value="2026-11-05", confirmed=True)
    assert earnings_label(event, now=NOW).startswith("today")


def test_earnings_dst_and_viewer_date_boundary():
    event = evidence(value="2026-11-01", scheduled_at=datetime(2026, 11, 1, 7, tzinfo=UTC))
    label = earnings_label(event, now=datetime(2026, 10, 31, 17, tzinfo=UTC))
    assert "1d" in label and "02:00 EST" in label
    assert earnings_label(event, now=NOW).startswith("past")


def test_no_source_grant_no_data_even_with_key(monkeypatch):
    monkeypatch.setenv("ANALYST_API_KEY", "not-a-real-key")
    assert corroborate([evidence()], CIK, "earnings", now=NOW)["status"] == "unavailable"


def test_corroboration_requires_independent_owner_and_surfaces_conflicts():
    items = [evidence(), evidence(provider="b")]
    grants = {"a": grant(), "b": grant("b", "owner-a")}
    assert corroborate(items, CIK, "earnings", now=NOW, grants=grants)["status"] == "single source"
    grants["b"] = grant("b", "owner-b")
    assert corroborate(items, CIK, "earnings", now=NOW, grants=grants)["status"] == "corroborated"
    items[1] = evidence(provider="b", value="2026-11-07")
    assert corroborate(items, CIK, "earnings", now=NOW, grants=grants)["status"] == "conflict"


@pytest.mark.parametrize("patch", [{"cik": "0000000001"}, {"url": "javascript:alert(1)"},
                                  {"as_of": NOW - timedelta(days=3)}, {"as_of": NOW + timedelta(seconds=1)},
                                  {"value": "bad"}, {"timezone": "bad/timezone"},
                                  {"scheduled_at": datetime(2026, 11, 8, tzinfo=UTC)}])
def test_rejects_unusable_earnings(patch):
    result = corroborate([evidence(**patch)], CIK, "earnings", now=NOW, grants={"a": grant()})
    assert result["status"] == "unavailable" and result["rejected"] == 1


def test_analyst_labels_attributed_not_averaged():
    item = evidence(field="analyst_sentiment", value="Neutral", sample_size=10)
    result = corroborate([item], CIK, "analyst_sentiment", now=NOW, grants={"a": grant()})
    assert result["evidence"][0].sample_size == 10
    assert result["status"] == "single source"
    assert corroborate([evidence(field="analyst_sentiment", value="Favorable")], CIK,
                       "analyst_sentiment", now=NOW, grants={"a": grant()})["status"] == "unavailable"


def test_company_brief_integration():
    responses = [Response({"0": {"cik_str": 320193, "title": "Fixture issuer", "ticker": "AAPL"}}),
                 Response({"cik": "0000320193", "filings": {"recent": {
                     "accessionNumber": [ACC], "filingDate": ["2026-11-01"], "form": ["10-K"],
                     "primaryDocument": ["annual.htm"]}}}), Response(facts())]
    client = gateway(lambda *args, **kwargs: responses.pop(0))
    result = company_deep_dive(client, "AAPL", now=NOW)
    assert result["company"].cik == CIK
    assert result["filings"][0]["form"] == "10-K"
    assert result["health"]["ratios"]["Net margin"] == .2
    assert result["earnings"]["status"] == result["analysts"]["status"] == "unavailable"
    assert len(result["sources"]) == 3
    assert all(set(source) == {"url", "retrieved_at"} for source in result["sources"])


def test_page_unconfigured_no_network(monkeypatch):
    monkeypatch.delenv("QI_SEC_USER_AGENT", raising=False)
    app = AppTest.from_string("from dashboard.discover_intelligence import render_intelligence\nrender_intelligence()")
    app.run()
    assert not app.exception
    assert "not connected" in app.info[0].value


def test_sec_budget_cooldown_and_spacing(monkeypatch):
    from app.intelligence import sec_access

    now = [1000.0]
    sleeps = []
    monkeypatch.setattr(sec_access.time, "time", lambda: now[0])

    def sleep(delay):
        sleeps.append(delay)
        now[0] += delay

    monkeypatch.setattr(sec_access.time, "sleep", sleep)
    monkeypatch.setattr(sec_access.requests, "get", lambda *a, **k: Response({}))
    sec_access.sec_get("https://data.sec.gov/test")
    sec_access.sec_get("https://data.sec.gov/test")
    assert sleeps == [0, 1]
    monkeypatch.setattr(sec_access.requests, "get", lambda *a, **k: Response({}, 429, {"Retry-After": "1200"}))
    sec_access.sec_get("https://data.sec.gov/test")
    with pytest.raises(RuntimeError, match="cooldown"):
        sec_access.sec_get("https://www.sec.gov/test")


def test_sec_budget_rejects_corrupt_state(monkeypatch):
    from pathlib import Path

    from app.intelligence import sec_access

    Path(sec_access.BUDGET_PATH).write_text("corrupt")
    with pytest.raises(RuntimeError, match="operator review"):
        sec_access.sec_get("https://data.sec.gov/test")


@pytest.mark.parametrize("bad", [None, [], "bad", {"Revenues": {"units": {"USD": [None, 1]}}}])
def test_malformed_financial_concepts_are_missing(bad):
    payload = {"cik": 320193, "facts": {"us-gaap": bad}}
    result = financial_health(payload, CIK, today=NOW.date())
    assert not result["ratios"] and result["issues"]


def test_configured_brief_ui_uses_provenance_and_comparison(monkeypatch):
    from dashboard import discover_intelligence as ui

    monkeypatch.setenv("QI_SEC_USER_AGENT", "Quant Intelligence research@operator.org")
    health = financial_health(facts(), CIK, today=NOW.date())
    from app.intelligence.company_identity import CompanyIdentity

    def brief(_gateway, ticker):
        return {"company": CompanyIdentity(ticker, "Fixture issuer", CIK), "health": health,
                "filings": [], "sources": [], "issues": [],
                "earnings": {"status": "unavailable", "evidence": []},
                "analysts": {"status": "unavailable", "evidence": []}}

    monkeypatch.setattr(ui, "company_deep_dive", brief)
    app = AppTest.from_string("from dashboard.discover_intelligence import render_intelligence\nrender_intelligence()")
    app.run()
    app.text_input[0].set_value("AAPL, MSFT")
    app.button[0].click().run()
    assert not app.exception
    app.multiselect[0].set_value(["AAPL", "MSFT"]).run()
    assert any(x.label == "Your comparison" for x in app.expander)
    next(b for b in app.button if b.key == "open_AAPL").click().run()
    assert any("Next investigation" in x.value for x in app.markdown)
    assert any("Current ratio" == x.label for x in app.metric)


def test_cash_profit_divergence_is_investigation_not_rating():
    from app.intelligence.discover_financials import health_observations

    payload = facts()
    row(payload, "NetCashProvidedByUsedInOperatingActivities")["val"] = -20
    result = financial_health(payload, CIK, today=NOW.date())
    assert any("different directions" in text for text in health_observations(result))
    row(payload, "NetCashProvidedByUsedInOperatingActivities")["accn"] = "0000320193-26-000002"
    result = financial_health(payload, CIK, today=NOW.date())
    assert not any("different directions" in text for text in health_observations(result))


def test_host_budget_serializes_separate_processes(tmp_path):
    import subprocess
    import sys

    path = str(tmp_path / "shared-budget.json")
    script = f'''
import time
from types import SimpleNamespace
from app.intelligence import sec_access
sec_access.BUDGET_PATH = {path!r}
def get(*args, **kwargs):
    print(time.time(), flush=True)
    return SimpleNamespace(status_code=200)
sec_access.requests.get = get
sec_access.sec_get("https://data.sec.gov/test")
'''
    children = [subprocess.Popen([sys.executable, "-c", script], stdout=subprocess.PIPE, text=True) for _ in range(2)]
    starts = []
    for child in children:
        output, _ = child.communicate(timeout=15)
        assert child.returncode == 0
        starts.append(float(output.strip()))
    assert abs(starts[1] - starts[0]) >= .95


def test_expired_or_incomplete_license_rejected():
    from dataclasses import replace

    for source in [replace(grant(), expires=date(2026, 1, 1)), replace(grant(), derived=False),
                   replace(grant(), display=False), replace(grant(), contract_reference="")]:
        assert corroborate([evidence()], CIK, "earnings", now=NOW, grants={"a": source})["status"] == "unavailable"


def test_cache_expiry_does_not_substitute_stale_facts():
    now = [0]
    calls = [Response({"cik": 320193}), RuntimeError("provider down")]

    def get(*args, **kwargs):
        response = calls.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    client = SecGateway("Quant Intelligence research@operator.org", get=get, clock=lambda: now[0], sleep=lambda x: None)
    client.fetch("companyfacts", CIK)
    now[0] = 3601
    with pytest.raises(RuntimeError, match="provider down"):
        client.fetch("companyfacts", CIK)


def test_screen_transparent_thresholds_and_no_missing_zero():
    from app.intelligence.discover_screen import screen_report

    health = financial_health(facts(), CIK, today=NOW.date())
    result = screen_report({"health": health}, today=NOW.date())
    assert result["eligible"] and result["matches"] == 4
    health["ratios"].pop("Current ratio")
    result = screen_report({"health": health}, today=NOW.date())
    assert result["matches"] is None
    assert result["checks"][-1]["passes"] is None


@pytest.mark.parametrize("patch", [
    {"period": "2020-01-01"}, {"period": "2027-01-01"},
    {"issues": ["Conflicting assets facts; excluded"]}, {"period": None},
])
def test_screen_excludes_stale_future_or_conflicting_evidence(patch):
    from app.intelligence.discover_screen import screen_report

    health = financial_health(facts(), CIK, today=NOW.date())
    health.update(patch)
    assert screen_report({"health": health}, today=NOW.date())["matches"] is None


def test_rank_is_deterministic_missing_last_and_not_investment_rating():
    from app.intelligence.company_identity import CompanyIdentity
    from app.intelligence.discover_screen import rank_reports

    def report(ticker, ratios):
        return {"company": CompanyIdentity(ticker, "QA issuer", CIK),
                "health": {"period": "2026-09-30", "issues": [], "ratios": ratios}}

    ratios = {"Net margin": .1, "Operating cash / revenue": .1,
              "Liabilities / assets": .6, "Current ratio": 1}
    rows = rank_reports([report("Z", ratios), report("M", {}), report("A", ratios)], today=NOW.date())
    assert [r["company"].ticker for r, _ in rows] == ["A", "Z", "M"]
    ratios["Net margin"] = float("nan")
    assert rank_reports([report("Z", ratios)], today=NOW.date())[0][1]["matches"] is None


def test_synthetic_candidate_filter_and_failed_refresh():
    app = AppTest.from_file(str(Path(__file__).parents[1] / "qa/discover_preview.py")).run()
    app.button[0].click().run()
    assert not app.exception
    assert any("4 of 4 criteria met" == x.value for x in app.markdown)
    next(b for b in app.button if b.key == "open_QAMISSING").click().run()
    assert any("Not ranked:" in x.value for x in app.markdown)
    next(b for b in app.button if b.label == "← Back to candidates").click().run()
    app.checkbox[0].check().run()
    assert any("4 of 4 criteria met" == x.value for x in app.markdown)
    app.text_input[0].set_value("QAERROR")
    app.button[0].click().run()
    assert not app.exception
    assert app.warning
    assert not app.session_state["qi_discover_reports"]


@pytest.mark.parametrize("route", ["💎 Quant Discovery", "🔍 Market Scanner"])
def test_main_discover_routes_render_native_candidates_without_external_panel(monkeypatch, route):
    from app.intelligence.company_identity import CompanyIdentity
    from dashboard import discover_intelligence as ui

    monkeypatch.setenv("QI_SEC_USER_AGENT", "offline fixture")
    monkeypatch.setattr(ui, "_gateway", lambda _: None)
    health = financial_health(facts(), CIK, today=NOW.date())
    health["period"] = datetime.now(UTC).date().isoformat()
    report = {"company": CompanyIdentity("AAPL", "Fixture issuer", CIK), "health": health,
              "filings": [], "sources": [], "issues": [],
              "earnings": {"status": "unavailable", "evidence": []},
              "analysts": {"status": "unavailable", "evidence": []}}
    monkeypatch.setattr(ui, "company_deep_dive", lambda *args: report)
    app = AppTest.from_file(str(Path(__file__).parents[1] / "dashboard/main.py"))
    app.session_state["selected_page"] = route
    app.run(timeout=45)
    next(button for button in app.button if button.label == "Find research candidates").click().run()
    assert not app.exception
    assert app.session_state["selected_page"] == "💎 Quant Discovery"
    assert any(item.value == "4 of 4 criteria met" for item in app.markdown)
    next(b for b in app.button if b.key == "open_AAPL").click().run()
    assert any(item.label == "Annual revenue" for item in app.metric)
    assert len(app.get("iframe")) == 0
    assert not any(toggle.key == "qi_discovery_consent" for toggle in app.toggle)


def test_discover_leads_with_evidence_not_dead_status_tiles(monkeypatch):
    monkeypatch.delenv("QI_SEC_USER_AGENT", raising=False)
    app = AppTest.from_string("from dashboard.discover_intelligence import render_intelligence\nrender_intelligence()").run()
    assert not app.exception
    assert not app.metric
    assert any(x.label == "Data coverage & setup" for x in app.expander)


def test_candidate_cards_show_annual_evidence_before_selection():
    app = AppTest.from_file(str(Path(__file__).parents[1] / "qa/discover_preview.py")).run()
    app.button[0].click().run()
    assert not app.exception
    text = "\n".join(x.value for x in app.markdown)
    assert "Synthetic QAALPHA" in text
    assert "Synthetic QAMISSING" in text
    assert any("Revenue: $1,000,000,000" in c.value for c in app.caption)
    assert any("Revenue: unavailable" in c.value for c in app.caption)
    next(b for b in app.button if b.key == "open_QAALPHA").click().run()
    text = "\n".join(x.value for x in app.markdown)
    assert "Reported: 20.0%" in text


def test_sec_directory_search_is_explicit_and_uses_verified_identity(monkeypatch):
    from dashboard import discover_intelligence as ui

    calls = []

    class Directory:
        def fetch(self, resource):
            calls.append(resource)
            return {"data": {"0": {"ticker": "AAPL", "title": "Apple Inc.", "cik_str": 320193}},
                    "retrieved_at": "2026-11-06T00:00:00+00:00"}

    monkeypatch.setenv("QI_SEC_USER_AGENT", "offline fixture")
    monkeypatch.setattr(ui, "_gateway", lambda _: Directory())
    app = AppTest.from_string("from dashboard.discover_intelligence import render_intelligence\nrender_intelligence()").run()
    assert not calls
    app.text_input[1].set_value("Apple")
    app.button[1].click().run()
    assert not app.exception
    assert calls == ["directory"]
    assert app.dataframe[0].value.iloc[0]["CIK"] == CIK
    assert "qi_discover_reports" not in app.session_state


def test_discover_search_compare_and_navigation_state(monkeypatch):
    monkeypatch.setenv("QI_QA_FACTORS", "1")
    app = AppTest.from_file(str(Path(__file__).parents[1] / "qa/discover_preview.py")).run()
    app.button[0].click().run()
    app.multiselect[0].set_value(["QAALPHA", "QABETA"]).run()
    assert len(app.dataframe[0].value) == 2
    app.text_input(key="qi_candidate_query").set_value("  qamissing  ").run()
    assert not app.exception
    assert not any(b.key == "open_QAALPHA" for b in app.button)
    assert any(b.key == "open_QAMISSING" for b in app.button)
    assert app.multiselect[0].value == ["QAALPHA", "QABETA"]
    app.text_input(key="qi_candidate_query").set_value("no such issuer").run()
    assert any("No candidates match" in i.value for i in app.info)
    app.text_input(key="qi_candidate_query").set_value("").run()
    app.selectbox(key="qi_candidate_sort").set_value("Company A–Z").run()
    assert [b.key for b in app.button if (b.key or "").startswith("open_")] == ["open_QAALPHA", "open_QABETA", "open_QAMISSING"]
    next(b for b in app.button if b.key == "open_QAALPHA").click().run()
    assert any("Synthetic QAALPHA" in h.value for h in app.subheader)
    next(b for b in app.button if b.label == "← Back to candidates").click().run()
    assert not app.subheader
    app.text_input[0].set_value("QAMISSING")
    app.button[0].click().run()
    assert not app.exception
    assert app.multiselect[0].value == []
    assert "qi_detail" not in app.session_state


def test_factor_display_units_and_missing():
    from dashboard.discover_intelligence import format_factor

    assert format_factor("cash_conversion", 1.25) == "1.25×"
    assert format_factor("margin_change", -.025) == "-2.5 pp"
    assert format_factor("revenue_cagr", .1) == "10.0%"
    assert format_factor("revenue_cagr", None) == "Unavailable"


def test_optional_research_evidence_and_original_check_failure_are_honest(monkeypatch):
    monkeypatch.setenv("QI_QA_FACTORS", "1")
    app = AppTest.from_file(str(Path(__file__).parents[1] / "qa/discover_preview.py")).run()
    app.button[0].click().run()
    assert app.radio[0].label == "Research pattern"
    next(b for b in app.button if b.key == "open_QAALPHA").click().run()
    assert not app.tabs
    assert {"Financial history", "How the pattern is calculated", "Try a business scenario", "Sources & evidence checks"} <= {e.label for e in app.expander}
    assert any("Sales grew" in m.value for m in app.markdown)
    assert any("Independent financial-source corroboration has not run" in i.value for i in app.info)
    next(b for b in app.button if b.key == "check_filing_QAALPHA").click().run()
    assert not app.exception
    assert any("Original filing check unavailable" in w.value for w in app.warning)
    assert "qi_filing_check_QAALPHA" not in app.session_state


def test_document_discrepancy_stays_visible_next_to_candidate(monkeypatch):
    monkeypatch.setenv("QI_QA_FACTORS", "1")
    app = AppTest.from_file(str(Path(__file__).parents[1] / "qa/discover_preview.py")).run()
    app.button[0].click().run()
    app.session_state["qi_filing_check_QAALPHA"] = {"rows": [{"Status": "discrepancy"}]}
    app.run()
    assert not app.exception
    assert any("Evidence discrepancy" in w.value for w in app.warning)
    assert any(b.key == "open_QAALPHA" for b in app.button)
