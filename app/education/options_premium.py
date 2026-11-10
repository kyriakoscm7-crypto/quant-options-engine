"""Deterministic European option teaching model, never a live market quote.

Black-Scholes analytical reference with zero continuously compounded rates and
zero dividends. Day-count basis ACT/365 and 252 trading days are deliberately
not mixed. Not intended for American equity option early-exercise decisions.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class OptionLessonValue:
    premium: float
    intrinsic: float
    time_value: float


def _number(name: str, value: float, lower: float, upper: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError(f"{name} must be a number.")
    n = float(value)
    if not math.isfinite(n) or not lower <= n <= upper:
        raise ValueError(f"{name} is outside the permitted learning range.")
    return n


def intrinsic_value(spot: float, strike: float, kind: str = "call") -> float:
    spot = _number("Stock price", spot, 0.01, 1_000_000)
    strike = _number("Strike price", strike, 0.01, 1_000_000)
    if kind not in {"call", "put"}:
        raise ValueError("Option type must be call or put.")
    return max(spot - strike, 0.0) if kind == "call" else max(strike - spot, 0.0)


def theoretical_option(spot: float, strike: float, days: int,
                       volatility_pct: float, kind: str = "call") -> OptionLessonValue:
    """Return theoretical premium and breakdown, all per underlying share.

    With no rates or dividends, a European option is worth no less than its
    intrinsic value. Zero remaining time returns exactly its payoff.
    """
    spot = _number("Stock price", spot, 0.01, 1_000_000)
    strike = _number("Strike price", strike, 0.01, 1_000_000)
    time_days = _number("Days to expiration", days, 0, 3650)
    sigma_pct = _number("Assumed annualized volatility", volatility_pct, 0, 300)
    intrinsic = intrinsic_value(spot, strike, kind)
    if time_days == 0 or sigma_pct == 0:
        return OptionLessonValue(intrinsic, intrinsic, 0.0)

    t = time_days / 365.0
    sigma = sigma_pct / 100.0
    sigma_t = sigma * math.sqrt(t)
    d1 = (math.log(spot / strike) + 0.5 * sigma * sigma * t) / sigma_t
    d2 = d1 - sigma_t

    def norm_cdf(x: float) -> float:
        return 0.5 * math.erfc(-x / math.sqrt(2.0))

    if kind == "call":
        price = spot * norm_cdf(d1) - strike * norm_cdf(d2)
    elif kind == "put":
        price = strike * norm_cdf(-d2) - spot * norm_cdf(-d1)
    else:
        raise ValueError("Option type must be call or put.")
    premium = max(intrinsic, price)
    return OptionLessonValue(premium, intrinsic, premium - intrinsic)


def expiration_profit(stock_at_expiry: float, strike: float,
                      premium_paid: float, kind: str = "call") -> float:
    """Long-option P/L per share at expiration, before fees."""
    premium_paid = _number("Premium paid", premium_paid, 0, 1_000_000)
    return intrinsic_value(stock_at_expiry, strike, kind) - premium_paid


def at_the_money_time_curve(days: list[int] | tuple[int, ...],
                            *, spot: float = 100, iv: float = 30) -> list[float]:
    return [
        theoretical_option(spot, spot, day, iv, "call").time_value
        for day in days
    ]
