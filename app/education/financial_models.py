
"""Educational financial simulations.

Illustrative calculations only, not personal financial advice.
No market prices, account information, or user data are collected.
"""

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class GrowthPoint:
    year: int
    balance: float
    contributed: float
    growth: float


@dataclass(frozen=True)
class DebtResult:
    months: int
    interest_paid: float
    total_paid: float


def compound_growth(
    starting_amount: float,
    monthly_contribution: float,
    annual_return_pct: float,
    years: int,
) -> tuple[GrowthPoint, ...]:
    """Model constant nominal annual return, compounded monthly.

    Contributions are added at each month's end.
    Fees, taxes, inflation, and market volatility are excluded.
    """
    amounts = (starting_amount, monthly_contribution, annual_return_pct)
    if not all(isfinite(v) for v in amounts):
        raise ValueError("All financial inputs must be finite.")
    if starting_amount < 0 or monthly_contribution < 0:
        raise ValueError("Savings and contributions cannot be negative.")
    if not isinstance(years, int) or isinstance(years, bool) or not 0 <= years <= 100:
        raise ValueError("Years must be between 0 and 100.")
    if annual_return_pct <= -100:
        raise ValueError("Annual return must exceed -100%.")

    balance = float(starting_amount)
    contributed = float(starting_amount)
    monthly_rate = annual_return_pct / 1200.0
    points = [GrowthPoint(0, balance, contributed, 0.0)]

    for year in range(1, years + 1):
        for _ in range(12):
            balance = balance * (1 + monthly_rate) + monthly_contribution
            contributed += monthly_contribution
        if not isfinite(balance):
            raise ValueError("The simulated balance exceeds numeric limits.")
        points.append(
            GrowthPoint(year, balance, contributed, balance - contributed)
        )

    return tuple(points)


def credit_card_payoff(
    starting_balance: float,
    annual_interest_pct: float,
    monthly_payment: float,
    max_months: int = 600,
) -> DebtResult:
    """Simplified monthly-interest debt payoff model.

    Interest is charged monthly before each payment.
    Fees, new purchases, and daily interest calculations are excluded.
    """
    inputs = (starting_balance, annual_interest_pct, monthly_payment)
    if not all(isfinite(v) for v in inputs):
        raise ValueError("All financial inputs must be finite.")
    if starting_balance < 0 or annual_interest_pct < 0 or monthly_payment < 0:
        raise ValueError("Inputs cannot be negative.")
    if not isinstance(max_months, int) or not 1 <= max_months <= 1200:
        raise ValueError("Invalid simulation horizon.")
    if starting_balance == 0:
        return DebtResult(0, 0.0, 0.0)

    monthly_rate = annual_interest_pct / 1200.0

    if monthly_payment <= starting_balance * monthly_rate:
        raise ValueError("Monthly payment does not cover initial interest.")

    balance = float(starting_balance)
    interest_paid = 0.0
    total_paid = 0.0

    for month in range(1, max_months + 1):
        interest = balance * monthly_rate
        payment = min(monthly_payment, balance + interest)
        balance = max(0.0, balance + interest - payment)
        interest_paid += interest
        total_paid += payment

        if balance < 0.005:
            return DebtResult(month, interest_paid, total_paid)

    raise ValueError("Debt was not repaid within the simulation horizon.")
