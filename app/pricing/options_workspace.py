"""Pure option research calculations using the existing pricing engine."""

from math import isfinite

from app.pricing.black_scholes import BlackScholes

CONTRACT_SIZE = 100


def _validate(spot, strike, days, volatility, rate, dividend):
    values = (spot, strike, days, volatility, rate, dividend)
    if not all(isinstance(x, (int, float)) and isfinite(x) for x in values):
        raise ValueError("All inputs must be finite numbers.")
    if spot <= 0 or strike <= 0 or days <= 0 or volatility <= 0:
        raise ValueError("Spot, strike, days and volatility must be positive.")


def theoretical_price(
    kind, spot, strike, days, volatility, rate=4.0, dividend=0.0
):
    """Black-Scholes European-style theoretical premium per share."""
    _validate(spot, strike, days, volatility, rate, dividend)
    if kind not in ("Call", "Put"):
        raise ValueError("Option must be Call or Put.")

    engine = BlackScholes(
        S=float(spot),
        K=float(strike),
        T=float(days) / 365,
        r=float(rate) / 100,
        sigma=float(volatility) / 100,
        q=float(dividend) / 100,
    )
    value = engine.call_price() if kind == "Call" else engine.put_price()
    return float(value)


def expiration_profit(kind, strike, premium, expiration_spot, contracts=1):
    """Long-option expiration profit, excluding fees, per position."""
    if kind not in ("Call", "Put"):
        raise ValueError("Option must be Call or Put.")
    if not all(isfinite(float(x)) for x in (
        strike, premium, expiration_spot, contracts
    )):
        raise ValueError("Finite inputs required.")
    if (
        strike <= 0 or premium < 0 or expiration_spot < 0
        or not isinstance(contracts, int) or contracts < 1
    ):
        raise ValueError("Invalid option position.")
    intrinsic = (
        max(expiration_spot - strike, 0)
        if kind == "Call"
        else max(strike - expiration_spot, 0)
    )
    return (intrinsic - premium) * CONTRACT_SIZE * contracts


def breakeven(kind, strike, premium):
    if kind not in ("Call", "Put") or strike <= 0 or premium < 0:
        raise ValueError("Invalid option.")
    return strike + premium if kind == "Call" else strike - premium


def scenario_mark_profit(
    kind, spot, strike, remaining_days, volatility,
    entry_premium, contracts=1, rate=4.0, dividend=0.0
):
    """Hypothetical marked-to-model P/L versus a fixed entry premium."""
    mark = theoretical_price(
        kind, spot, strike, remaining_days, volatility, rate, dividend
    )
    return (mark - entry_premium) * CONTRACT_SIZE * contracts
