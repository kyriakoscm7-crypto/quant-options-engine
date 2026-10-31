"""Deterministic fictional portfolio stress tests for education.

All values and returns are invented to illustrate portfolio exposure.
They are not forecasts, historical observations or risk estimates.
"""

PORTFOLIOS = {
    "Concentrated": {
        "Company A": 70,
        "Company B": 10,
        "Company C": 10,
        "Company D": 10,
        "Company E": 0,
    },
    "Evenly spread": {
        "Company A": 25,
        "Company B": 25,
        "Company C": 25,
        "Company D": 25,
        "Company E": 0,
    },
    "Broader mix": {
        "Company A": 10,
        "Company B": 20,
        "Company C": 20,
        "Company D": 20,
        "Company E": 30,
    },
}

EVENTS = {
    "One company disappoints": {
        "Company A": -30,
        "Company B": 0,
        "Company C": 0,
        "Company D": 0,
        "Company E": 0,
    },
    "A sector faces pressure": {
        "Company A": -30,
        "Company B": -25,
        "Company C": 0,
        "Company D": 0,
        "Company E": 0,
    },
    "A broad market sell-off": {
        "Company A": -30,
        "Company B": -20,
        "Company C": -15,
        "Company D": -10,
        "Company E": -8,
    },
}

def stress_test(weights, returns, starting_value=1000):
    """Apply one-period holding returns using starting portfolio weights."""
    if not weights or set(weights) != set(returns):
        raise ValueError("Weights and returns must cover the same holdings.")
    if any(not isinstance(v, (int, float)) or v < 0 for v in weights.values()):
        raise ValueError("Portfolio weights must be nonnegative numbers.")
    if abs(sum(weights.values()) - 100) > 1e-8:
        raise ValueError("Portfolio weights must total 100%.")
    if any(
        not isinstance(v, (int, float)) or not -100 <= v <= 1000
        for v in returns.values()
    ):
        raise ValueError("Invalid hypothetical holding return.")
    if not isinstance(starting_value, (int, float)) or starting_value < 0:
        raise ValueError("Invalid starting value.")

    details = []
    total_change = 0.0
    for name, weight in weights.items():
        before = starting_value * weight / 100
        change = before * returns[name] / 100
        total_change += change
        details.append({
            "holding": name,
            "weight": weight,
            "return": returns[name],
            "change": change,
            "after": before + change,
        })

    return {
        "start": float(starting_value),
        "change": total_change,
        "end": starting_value + total_change,
        "return_pct": total_change / starting_value * 100
        if starting_value else 0,
        "details": details,
    }
