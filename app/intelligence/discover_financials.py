"""Conservative annual US-GAAP observations, with filing-level provenance.

Only comparable, full-year, USD, 10-K facts are used. No quarterly annualization,
sector ratings, valuation claims or synthetic missing values.
"""
import math
from datetime import date

from app.intelligence.sec_filings import ACCESSION_PATTERN, filings_near_event

TAGS = {
    "assets": ("Assets",),
    "liabilities": ("Liabilities",),
    "current_assets": ("AssetsCurrent",),
    "current_liabilities": ("LiabilitiesCurrent",),
    "revenue": ("RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"),
    "income": ("NetIncomeLoss",),
    "operating_cash": ("NetCashProvidedByUsedInOperatingActivities",),
}
DURATION = {"revenue", "income", "operating_cash"}


def normalized_filings(submissions, cik, today=None):
    """Recent valid filing links; amendments remain separate, never overwritten."""
    today = today or date.today()
    return filings_near_event(submissions, int(cik), today, before_days=730, after_days=0, limit=100)


def financial_health(companyfacts, cik, *, today=None):
    today = today or date.today()
    if str(companyfacts.get("cik", "")).lstrip("0") != str(cik).lstrip("0"):
        raise ValueError("Financial facts CIK does not match verified company")
    root = companyfacts.get("facts", {})
    facts = root.get("us-gaap", {}) if isinstance(root, dict) else {}
    if not isinstance(facts, dict):
        facts = {}
    candidates = {}
    for metric, tags in TAGS.items():
        rows = []
        for tag in tags:
            concept = facts.get(tag, {})
            units = concept.get("units", {}) if isinstance(concept, dict) else {}
            values = units.get("USD", []) if isinstance(units, dict) else []
            for row in values if isinstance(values, list) else []:
                if not isinstance(row, dict):
                    continue
                try:
                    end, filed = date.fromisoformat(row["end"]), date.fromisoformat(row["filed"])
                    value = row["val"]
                    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                        continue
                    if row["form"] not in {"10-K", "10-K/A"} or not ACCESSION_PATTERN.fullmatch(row["accn"]):
                        continue
                    if not end <= filed <= today:
                        continue
                    start = row.get("start")
                    if metric in DURATION:
                        if not 330 <= (end - date.fromisoformat(start)).days <= 380:
                            continue
                    elif start:
                        continue
                    rows.append({"metric": metric, "tag": tag, "value": value, "unit": "USD",
                                 "start": start, "end": end.isoformat(), "filed": filed.isoformat(),
                                 "form": row["form"], "accession": row["accn"],
                                 "url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{row['accn'].replace('-', '')}/"})
                except (KeyError, TypeError, ValueError):
                    continue
        candidates[metric] = rows
    # Anchor all observations to the latest full-year duration; do not silently
    # present an older complete year as the latest year when recent tags are absent.
    ends = [r["end"] for key in DURATION for r in candidates[key]]
    period = max(ends) if ends else None
    observations, issues = {}, []
    for metric, rows in candidates.items():
        rows = [r for r in rows if r["end"] == period]
        if not rows:
            issues.append(f"Missing comparable annual {metric}")
            continue
        latest_filed = max(r["filed"] for r in rows)
        latest = [r for r in rows if r["filed"] == latest_filed]
        contexts = {(r["value"], r["start"], r["accession"]) for r in latest}
        if len(contexts) != 1:
            issues.append(f"Conflicting {metric} facts; excluded")
            continue
        observations[metric] = latest[0]
        if len({r["value"] for r in rows}) > 1:
            issues.append(f"{metric}: revised historical values; latest filing used")
    ratios = {}
    for name, numerator, denominator in (
        ("Current ratio", "current_assets", "current_liabilities"),
        ("Liabilities / assets", "liabilities", "assets"),
        ("Net margin", "income", "revenue"),
        ("Operating cash / revenue", "operating_cash", "revenue"),
    ):
        a, b = observations.get(numerator), observations.get(denominator)
        if a and b and a["accession"] == b["accession"] and a["start"] == b["start"] and b["value"] > 0:
            ratios[name] = a["value"] / b["value"]
        else:
            issues.append(f"{name} unavailable: missing, nonpositive denominator or incompatible filing context")
    if period and (today - date.fromisoformat(period)).days > 550:
        issues.append("Annual period is older than 550 days")
    return {"period": period, "observations": observations, "ratios": ratios, "issues": issues,
            "status": "partial" if issues else "single source", "source": "SEC EDGAR / issuer-reported US-GAAP"}


def health_observations(health):
    """Plain descriptions of reported quantities, without investment ratings."""
    ratios = health["ratios"]
    notes = []
    if "Current ratio" in ratios and ratios["Current ratio"] < 1:
        notes.append("Reported current liabilities exceed current assets. Investigate liquidity, working-capital timing and sector context.")
    if "Liabilities / assets" in ratios and ratios["Liabilities / assets"] > 1:
        notes.append("Reported liabilities exceed assets. Review the equity deficit and accounting context in the filing.")
    income = health["observations"].get("income")
    cash = health["observations"].get("operating_cash")
    if income and income["value"] < 0:
        notes.append("The issuer reported an annual net loss. Examine recurring operations and exceptional charges.")
    if cash and cash["value"] < 0:
        notes.append("Annual operations used cash. Review funding needs and the cash-flow statement.")
    if income and cash and income["accession"] == cash["accession"] and income["start"] == cash["start"] and income["value"] > 0 > cash["value"]:
        notes.append("Reported profit and operating cash flow point in different directions. Investigate working capital and noncash items.")
    return notes or ["Read the full statements and risk factors. These annual ratios alone do not establish business quality or a suitable valuation."]
