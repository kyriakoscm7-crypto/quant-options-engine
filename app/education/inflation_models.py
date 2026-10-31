"""Inflation and purchasing-power models for financial education.

All rates are hypothetical, not predictions or live economic data.
"""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class InflationResult:
    future_price: float
    future_savings: float
    savings_in_today_dollars: float
    purchasing_power_change_pct: float


def purchasing_power(
    starting_price: float,
    savings: float,
    inflation_pct: float,
    savings_return_pct: float,
    years: int,
) -> InflationResult:
    """Compare hypothetical future prices and savings purchasing power.

    Assumes constant annual inflation and savings returns,
    compounded annually, with no additions or withdrawals.
    """

    values = (
        starting_price,
        savings,
        inflation_pct,
        savings_return_pct,
    )

    if not all(isfinite(v) for v in values):
        raise ValueError("Inputs must be finite.")

    if starting_price < 0 or savings < 0:
        raise ValueError("Prices and savings cannot be negative.")

    if inflation_pct <= -100 or savings_return_pct <= -100:
        raise ValueError("Annual rates must exceed -100%.")

    if inflation_pct > 100 or savings_return_pct > 100:
        raise ValueError("Annual rates exceed supported range.")

    if type(years) is not int or not 0 <= years <= 100:
        raise ValueError("Years must be an integer between 0 and 100.")

    price_factor = (1 + inflation_pct / 100) ** years
    savings_factor = (1 + savings_return_pct / 100) ** years

    future_price = starting_price * price_factor
    future_savings = savings * savings_factor
    real_savings = future_savings / price_factor

    if not all(isfinite(v) for v in (
        future_price, future_savings, real_savings
    )):
        raise ValueError("Calculated values exceed numeric limits.")

    change = (
        (real_savings / savings - 1) * 100
        if savings > 0 else 0.0
    )

    return InflationResult(
        future_price=future_price,
        future_savings=future_savings,
        savings_in_today_dollars=real_savings,
        purchasing_power_change_pct=change,
    )


def real_return_pct(
    nominal_return_pct: float,
    inflation_pct: float,
) -> float:
    """Exact inflation-adjusted annual return, expressed in percent."""

    if not all(isfinite(v) for v in (
        nominal_return_pct, inflation_pct
    )):
        raise ValueError("Rates must be finite.")

    if nominal_return_pct <= -100 or inflation_pct <= -100:
        raise ValueError("Rates must exceed -100%.")

    return (
        (1 + nominal_return_pct / 100)
        / (1 + inflation_pct / 100)
        - 1
    ) * 100
