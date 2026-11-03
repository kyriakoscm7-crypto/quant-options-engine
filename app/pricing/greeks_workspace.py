"""Option Greeks and local price approximation calculations."""

from math import isfinite

from app.pricing.black_scholes import BlackScholes


def calculate_greeks(kind, spot, strike, days, volatility, rate=4.0, dividend=0.0):
    if kind not in ("Call", "Put"):
        raise ValueError("Option must be Call or Put.")
    values = (spot, strike, days, volatility, rate, dividend)
    if not all(isinstance(x, (int, float)) and isfinite(x) for x in values):
        raise ValueError("All inputs must be finite.")
    if spot <= 0 or strike <= 0 or days <= 0 or volatility <= 0:
        raise ValueError("Spot, strike, time and volatility must be positive.")

    engine = BlackScholes(
        S=float(spot), K=float(strike), T=float(days) / 365,
        r=float(rate) / 100, sigma=float(volatility) / 100,
        q=float(dividend) / 100,
    )
    result = engine.greeks()
    prefix = "call" if kind == "Call" else "put"

    return {
        "price": float(result[f"{prefix}_price"]),
        "delta": float(result[f"{prefix}_delta"]),
        "gamma": float(result["gamma"]),
        "vega": float(result["vega"]),
        "theta": float(result[f"{prefix}_theta"]),
        "rho": float(result[f"{prefix}_rho"]),
    }


def compare_repricing(kind, spot, strike, days, volatility, move,
                      rate=4.0, dividend=0.0):
    """Compare local Delta-Gamma approximation with full Black-Scholes."""
    initial = calculate_greeks(
        kind, spot, strike, days, volatility, rate, dividend
    )
    new_spot = spot + move
    if not isfinite(new_spot) or new_spot <= 0:
        raise ValueError("Scenario underlying must be positive.")

    updated = calculate_greeks(
        kind, new_spot, strike, days, volatility, rate, dividend
    )
    approx = (
        initial["price"] + initial["delta"] * move
        + 0.5 * initial["gamma"] * move * move
    )
    return {
        "initial": initial,
        "new_spot": new_spot,
        "full_price": updated["price"],
        "approx_price": approx,
        "approx_error": approx - updated["price"],
    }
