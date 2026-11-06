"""Transparent annual-fundamental screening; no return forecasts or hidden scores."""
from datetime import UTC, date, datetime
from math import isfinite

# Small editorial starting universes, not index membership or recommendations.
UNIVERSES = {
    "Large company starting set": ("AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA"),
    "Consumer & industrial starting set": ("WMT", "COST", "PG", "KO", "CAT", "DE"),
}
RULES = {
    "Net margin": ("Net margin ≥ 10%", lambda x: x >= .10),
    "Operating cash / revenue": ("Operating cash / revenue ≥ 10%", lambda x: x >= .10),
    "Liabilities / assets": ("Liabilities / assets ≤ 60%", lambda x: 0 <= x <= .60),
    "Current ratio": ("Current ratio ≥ 1", lambda x: x >= 1),
}


def screen_report(report, *, today=None):
    """Only rank complete, recent, conflict-free annual ratios; missing isn't zero."""
    today = today or datetime.now(UTC).date()
    health = report.get("health") or {}
    ratios = health.get("ratios", {})
    try:
        age = (today - date.fromisoformat(health.get("period", ""))).days
        recent = 0 <= age <= 550
    except (TypeError, ValueError):
        recent = False
    conflict = any("conflict" in issue.lower() for issue in health.get("issues", []))
    checks = []
    for key, (label, rule) in RULES.items():
        value = ratios.get(key)
        available = isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value)
        checks.append({"factor": key, "criterion": label, "value": value if available else None,
                       "passes": rule(value) if available else None})
    eligible = recent and not conflict and all(x["passes"] is not None for x in checks)
    return {"checks": checks, "eligible": eligible,
            "matches": sum(x["passes"] is True for x in checks) if eligible else None,
            "reason": "Comparable annual evidence" if eligible else
            "Not ranked: missing, conflicting or older than 550 days annual evidence"}


def rank_reports(reports, *, today=None):
    rows = [(report, screen_report(report, today=today)) for report in reports]
    return sorted(rows, key=lambda row: (not row[1]["eligible"],
                  -(row[1]["matches"] or 0), row[0]["company"].ticker))
